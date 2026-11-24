"""Admin moderation rules for courses, sections, and lectures."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.core.email_notifications import notify_course_learners, notify_moderators
from apps.core.schema import SubmissionResponseSerializer


class InstructorStatusReadOnlyMixin:
    """Keep content status changes in the admin moderation workflow."""

    def _is_instructor_request(self):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and not user.is_admin)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._is_instructor_request():
            self.fields["status"].read_only = True

    def to_internal_value(self, data):
        if self._is_instructor_request() and "status" in data:
            raise ValidationError(
                {"status": "Submit this content for review instead of setting status."}
            )
        return super().to_internal_value(data)


class AdminStatusOnlyMixin:
    """Admins may update only status and delete without restoring content."""

    admin_delete_status = status.HTTP_204_NO_CONTENT

    def update(self, request, *args, **kwargs):
        if request.user.is_admin:
            if set(request.data) - {"status"}:
                raise PermissionDenied("Admins may only update status.")
            # PUT must not require the metadata that admins cannot edit.
            kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def perform_update(self, serializer):
        instance = serializer.instance
        old_status = instance.status
        material_fields = {
            "course": {
                "title",
                "short_description",
                "long_description",
                "requirements",
                "learn_description_points",
                "total_hours",
                "price",
                "localization",
                "categories",
            },
            "section": {"title", "description", "order"},
            "lecture": {
                "title",
                "description",
                "source",
                "document_content",
                "resources",
                "order",
                "lecture_type",
            },
        }.get(instance._meta.model_name, set())
        previous_values = self._snapshot_material_fields(instance, material_fields)
        instance = serializer.save()

        if old_status != instance.status:
            reject_reason = getattr(instance, "reject_reason", "")
            reason = f" Reason: {reject_reason}" if reject_reason else ""
            queue_status_email = self.queue_status_email
            queue_status_email(instance, reason=reason)

        changed_fields = self._changed_material_fields(
            instance, material_fields, previous_values
        )
        published_transition = old_status != instance.status and (
            old_status == "published" or instance.status == "published"
        )
        if changed_fields or published_transition:
            course = getattr(instance, "course", instance)
            if published_transition:
                message = (
                    f'The {self.submission_label.lower()} "{instance.title}" '
                    f'in "{course.title}" is now {instance.status}.'
                )
            else:
                message = (
                    f'The {self.submission_label.lower()} "{instance.title}" '
                    f'in "{course.title}" was updated.'
                )
            notify_course_learners(
                course,
                subject=f"Course update: {course.title}",
                title="A course you are enrolled in was updated",
                message=message,
            )

    def _snapshot_material_fields(self, instance, fields):
        snapshot = {}
        for field_name in fields:
            if field_name not in instance._meta.fields_map and not any(
                field.name == field_name for field in instance._meta.get_fields()
            ):
                continue
            field = instance._meta.get_field(field_name)
            value = getattr(instance, field_name)
            snapshot[field_name] = (
                set(value.values_list("pk", flat=True)) if field.many_to_many else value
            )
        return snapshot

    def _changed_material_fields(self, instance, fields, previous_values):
        changed = set()
        for field_name in fields:
            if field_name not in previous_values:
                continue
            field = instance._meta.get_field(field_name)
            value = getattr(instance, field_name)
            current = (
                set(value.values_list("pk", flat=True)) if field.many_to_many else value
            )
            if current != previous_values[field_name]:
                changed.add(field_name)
        return changed

    def queue_status_email(self, instance, *, reason):
        from apps.core.email_notifications import queue_notification_email

        status_label = instance.get_status_display()
        queue_notification_email(
            instance.instructor,
            subject=f"{self.submission_label} status updated: {status_label}",
            title=f"{self.submission_label} {status_label.lower()}",
            message=(
                f'Your {self.submission_label.lower()} "{instance.title}" status '
                f"is now {status_label.lower()}.{reason}"
            ),
        )

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return self._destroy_instructor(request, *args, **kwargs)
        instance = self.get_object()
        if not instance.is_deleted:
            instance.soft_delete()
            course = getattr(instance, "course", instance)
            notify_course_learners(
                course,
                subject=f"Course update: {course.title}",
                title="Course content was removed",
                message=(
                    f'The {self.submission_label.lower()} "{instance.title}" '
                    f'in "{course.title}" is no longer available.'
                ),
            )
        if self.admin_delete_status == status.HTTP_204_NO_CONTENT:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"message": "Lecture deleted successfully"},
            status=self.admin_delete_status,
        )


class InstructorSubmissionMixin:
    """Allow instructors to submit owned content for admin publication review."""

    submission_label = "Content"

    @extend_schema(
        responses={200: SubmissionResponseSerializer},
        description=(
            "Submit instructor-owned content for admin review. The content becomes "
            "public only after an administrator approves it."
        ),
    )
    @action(detail=True, methods=["post"], url_path="submit")
    def submit_for_review(self, request, *args, **kwargs):
        instance = self.get_object()
        self.validate_submission(instance)
        if instance.status == "published":
            raise ValidationError(
                {"detail": f"{self.submission_label} is already published."}
            )
        if instance.status == "in-review":
            raise ValidationError(
                {"detail": f"{self.submission_label} is already awaiting review."}
            )

        instance.status = "in-review"
        instance.save(update_fields=["status", "updated_at"])
        notify_moderators(
            subject=f"{self.submission_label} submitted for review",
            title="Content submitted for review",
            message=(
                f'{self.submission_label} "{instance.title}" from '
                f"{instance.instructor.get_full_name() or instance.instructor.email} "
                "is awaiting moderation."
            ),
        )
        return Response(
            {
                "message": (
                    f"{self.submission_label} submitted for review. "
                    "It will be published once an admin approves it."
                ),
                "status": instance.status,
            },
            status=status.HTTP_200_OK,
        )

    def validate_submission(self, instance):
        if instance.status not in {"draft", "rejected", "approved"}:
            raise ValidationError(
                {"detail": f"{self.submission_label} cannot be submitted for review."}
            )
