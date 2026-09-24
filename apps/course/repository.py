from .models import Course


class CourseRepository:
    """
    Repository to handle database interactions for Course.
    """

    @staticmethod
    def annotate_course_queryset(queryset):
        return queryset

    @staticmethod
    def get_published_courses():
        queryset = Course.objects.filter(
            deleted_at__isnull=True,
            status="published",
            instructor__status="AC",
        ).order_by("-created_at")
        return CourseRepository.annotate_course_queryset(queryset)

    @staticmethod
    def get_courses_by_category(category):
        queryset = Course.objects.filter(
            deleted_at__isnull=True,
            status="published",
            instructor__status="AC",
            categories=category,
        ).order_by("-created_at")
        return CourseRepository.annotate_course_queryset(queryset)

    @staticmethod
    def get_user_courses(user):
        if getattr(user, "is_admin", False):
            return Course.objects.all()
        return Course.objects.filter(deleted_at__isnull=True, instructor=user)

    @staticmethod
    def get_all_courses():
        return Course.objects.all()

    @staticmethod
    def create_course(**kwargs):
        return Course.objects.create(**kwargs)

    @staticmethod
    def update_course(course, **kwargs):
        for field, value in kwargs.items():
            setattr(course, field, value)
        course.save()
        return course

    @staticmethod
    def soft_delete_course(course):
        return course.soft_delete()

    @staticmethod
    def restore_course(course):
        return course.restore()

    @staticmethod
    def toggle_course_status(course):
        return course.toggle_deleted()
