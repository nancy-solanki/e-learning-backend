from .models import Section


class SectionRepository:
    """
    Repository to handle database interactions for Section.
    """

    @staticmethod
    def get_all_published_sections():
        return Section.objects.filter(
            deleted_at__isnull=True,
            instructor__status="AC",
            status=Section.Status.PUBLISHED,
        ).order_by("order")

    @staticmethod
    def get_section_by_slug(slug):
        return Section.objects.filter(slug=slug).first()

    @staticmethod
    def get_sections_by_course(course):
        return Section.objects.filter(deleted_at__isnull=True, course=course).order_by(
            "order"
        )

    @staticmethod
    def get_published_sections_by_course(course):
        return Section.objects.filter(
            deleted_at__isnull=True, status=Section.Status.PUBLISHED, course=course
        ).order_by("order")

    @staticmethod
    def get_user_sections(user):
        if getattr(user, "is_admin", False):
            return Section.objects.all().order_by("order")
        return Section.objects.filter(
            deleted_at__isnull=True, instructor=user
        ).order_by("order")

    @staticmethod
    def create_section(**kwargs):
        return Section.objects.create(**kwargs)

    @staticmethod
    def update_section(section, **kwargs):
        for field, value in kwargs.items():
            setattr(section, field, value)
        section.save()
        return section

    @staticmethod
    def soft_delete_section(section):
        return section.soft_delete()

    @staticmethod
    def restore_section(section):
        return section.restore()

    @staticmethod
    def toggle_section_status(section):
        return section.toggle_deleted()
