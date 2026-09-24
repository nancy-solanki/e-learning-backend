from .repository import CourseRepository


class CourseService:
    """
    Service to handle business logic for Course.
    """

    @staticmethod
    def get_public_queryset():
        return CourseRepository.get_published_courses()

    @staticmethod
    def get_queryset_for_user(user):
        return CourseRepository.get_user_courses(user)

    @staticmethod
    def get_courses_by_category(category):
        return CourseRepository.get_courses_by_category(category)

    @staticmethod
    def toggle_course_status(course):
        return CourseRepository.toggle_course_status(course)

    @staticmethod
    def create_course(**kwargs):
        return CourseRepository.create_course(**kwargs)

    @staticmethod
    def update_course(course, **kwargs):
        return CourseRepository.update_course(course, **kwargs)
