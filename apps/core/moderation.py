"""Admin moderation rules for courses, sections, and lectures."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

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

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return self._destroy_instructor(request, *args, **kwargs)
        instance = self.get_object()
        if not instance.is_deleted:
            instance.soft_delete()
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
