from .repository import EnrollRepository


class EnrollService:
    """
    Service to handle business logic relating to the Enroll model.
    """

    @staticmethod
    def get_enrollments(user):
        """Returns enrollments based on user role."""
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
        return "Successfully enrolled"

    @staticmethod
    def get_enrollments_by_course(slug):
        """Returns enrollments for a specific course slug."""
        return EnrollRepository.get_enrollments_by_course_slug(slug)
