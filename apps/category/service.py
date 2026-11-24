from apps.common.service import FileService
from apps.core.email_notifications import queue_notification_email
from apps.course.models import Course
from apps.enroll.models import Enroll
from apps.users.models import User

from .repository import CategoryRepository


class CategoryService:
    """
    Service to handle business logic for Category.
    """

    @staticmethod
    def _resolve_thumbnail(thumbnail):
        if isinstance(thumbnail, (list, tuple)):
            return thumbnail[0] if thumbnail else None
        return thumbnail

    @staticmethod
    def get_queryset_for_user(user):
        return CategoryRepository.get_active_categories()

    @staticmethod
    def upload_thumbnail(thumbnail):
        file_obj = CategoryService._resolve_thumbnail(thumbnail)
        if not file_obj:
            raise ValueError("Thumbnail is required.")
        return FileService.upload_file_to_cloud(file_obj, "category")

    @staticmethod
    def update_category(category, data, thumbnail=None):
        data = data.copy()
        if thumbnail is not None:
            data["thumbnail"] = CategoryService.upload_thumbnail(thumbnail)
        return CategoryRepository.update_category(category, **data)

    @staticmethod
    def delete_category(category):
        return CategoryRepository.soft_delete_category(category)

    @staticmethod
    def notify_instructors(category, *, event: str, previous_title: str = ""):
        if event == "created":
            instructors = User.objects.filter(
                groups__name="instructor",
                is_active=True,
                status=User.Status.ACTIVE,
                email_notifications=True,
            ).distinct()
            subject = f"New course category: {category.title}"
            title = "A new course category is available"
            message = f'The "{category.title}" category has been added to the catalog.'
        else:
            instructor_ids = (
                Course.objects.filter(
                    categories=category,
                    deleted_at__isnull=True,
                )
                .values_list("instructor_id", flat=True)
                .distinct()
            )
            instructors = User.objects.filter(
                pk__in=instructor_ids,
                is_active=True,
                status=User.Status.ACTIVE,
                email_notifications=True,
            )
            if event == "renamed":
                subject = f"Course category renamed: {category.title}"
                title = "A course category was renamed"
                message = (
                    f'The "{previous_title}" category is now named '
                    f'"{category.title}". Please review your course listings.'
                )
            else:
                subject = f"Course category removed: {category.title}"
                title = "A course category was removed"
                message = (
                    f'The "{category.title}" category has been removed. '
                    "Please review the categories assigned to your courses."
                )

            # A rename or removal changes how enrolled learners can find the
            # course in the catalog, so send one notice per learner even if
            # they are enrolled in several courses using this category.
            course_ids = Course.objects.filter(
                categories=category,
                deleted_at__isnull=True,
            ).values_list("pk", flat=True)
            learner_ids = (
                Enroll.objects.filter(
                    course_id__in=course_ids,
                    deleted_at__isnull=True,
                )
                .values_list("user_id", flat=True)
                .distinct()
            )
            learners = User.objects.filter(
                pk__in=learner_ids,
                is_active=True,
                status=User.Status.ACTIVE,
                email_notifications=True,
            )
            learner_subject = subject.replace("Course category", "Course catalog")
            learner_title = title.replace("category", "course catalog")
            for learner in learners.iterator(chunk_size=500):
                queue_notification_email(
                    learner,
                    subject=learner_subject,
                    title=learner_title,
                    message=message,
                )

        for instructor in instructors.iterator(chunk_size=500):
            queue_notification_email(
                instructor,
                subject=subject,
                title=title,
                message=message,
            )
