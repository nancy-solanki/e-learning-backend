from apps.core.email_notifications import queue_notification_email

from .repository import EnrollRepository


class EnrollService:
    """
    Service to handle business logic relating to the Enroll model.
    """

    @staticmethod
    def get_enrollments(user):
        """Returns enrollments based on user role."""
        if user.is_admin:
            return EnrollRepository.get_all_enrollments()
        if user.is_instructor:
            return EnrollRepository.get_instructor_enrollments(user)
        return EnrollRepository.get_user_enrollments(user)

    @staticmethod
    def enroll_user_in_course(user, course) -> str:
        """Enrolls a user in a course."""
        # Add enrollment logic (e.g., check if already enrolled)
        existing_enrollment = EnrollRepository.get_user_enrollments(user).filter(
            course=course
        )
        if existing_enrollment.exists():
            return "Already enrolled"

        EnrollRepository.create_enrollment(user, course)
        queue_notification_email(
            user,
            subject=f"Enrollment confirmed: {course.title}",
            title="You are enrolled",
            message=f'Your enrollment in "{course.title}" is confirmed.',
            preference_required=False,
        )
        queue_notification_email(
            course.instructor,
            subject=f"New learner in {course.title}",
            title="A learner enrolled in your course",
            message=(
                f'{user.get_full_name() or user.email} enrolled in "{course.title}".'
            ),
        )
        return "Successfully enrolled"

    @staticmethod
    def revoke_enrollment(enrollment):
        EnrollRepository.delete_enrollment(enrollment)
        queue_notification_email(
            enrollment.user,
            subject=f"Course access revoked: {enrollment.course.title}",
            title="Course access was revoked",
            message=(
                f'Your access to "{enrollment.course.title}" has been revoked. '
                "Contact support if you believe this is a mistake."
            ),
            preference_required=False,
        )
        return "Enrollment revoked"

    @staticmethod
    def get_enrollments_by_course(slug):
        """Returns enrollments for a specific course slug."""
        return EnrollRepository.get_enrollments_by_course_slug(slug)
