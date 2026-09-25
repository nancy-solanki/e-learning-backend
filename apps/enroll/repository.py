from .models import Enroll


class EnrollRepository:
    """
    Repository to handle database interactions relating to the Enroll model.
    """

    @staticmethod
    def get_all_enrollments():
        """Returns a queryset of all active enrollments (not deleted)."""
        return Enroll.objects.filter(deleted_at__isnull=True).order_by("-created_at")

    @staticmethod
    def get_instructor_enrollments(user):
        """Returns a queryset of enrollments for courses belonging to the instructor."""
        return Enroll.objects.filter(
            deleted_at__isnull=True, course__instructor=user
        ).order_by("-created_at")

    @staticmethod
    def get_user_enrollments(user):
        """Returns a queryset of enrollments for a specific user."""
        return Enroll.objects.filter(deleted_at__isnull=True, user=user).order_by(
            "-created_at"
        )

    @staticmethod
    def get_enrollments_by_course(course):
        """Returns enrollments for a specific course."""
        return Enroll.objects.filter(deleted_at__isnull=True, course=course).order_by(
            "-created_at"
        )

    @staticmethod
    def get_enrollments_by_course_slug(slug):
        """Returns enrollments for a course slug."""
        return Enroll.objects.filter(
            deleted_at__isnull=True, course__slug=slug, course__status="published"
        ).order_by("-created_at")

    @staticmethod
    def create_enrollment(user, course):
        """Creates a new enrollment."""
        return Enroll.objects.create(user=user, course=course)

    @staticmethod
    def delete_enrollment(enrollment):
        """Soft deletes an enrollment."""
        return enrollment.soft_delete()
