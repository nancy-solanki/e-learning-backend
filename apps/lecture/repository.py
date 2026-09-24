from .models import Lecture


class LectureRepository:
    """
    Repository to handle database interactions relating to the Lecture model.
    """

    @staticmethod
    def get_active_lectures():
        """Returns a queryset of active lectures."""
        return Lecture.objects.filter(
            deleted_at__isnull=True, instructor__status="AC", status="published"
        ).order_by("order")

    @staticmethod
    def get_instructor_lectures(user):
        """Returns a queryset of lectures for a specific instructor."""
        return Lecture.objects.filter(
            deleted_at__isnull=True, instructor=user
        ).order_by("order")

    @staticmethod
    def get_all_lectures():
        """Returns a queryset of all lectures (not deleted)."""
        return Lecture.objects.filter(deleted_at__isnull=True).order_by("order")

    @staticmethod
    def get_admin_lectures():
        """Returns a queryset of all lectures for admin."""
        return Lecture.objects.all().order_by("order")

    @staticmethod
    def get_lectures_by_section(section):
        """Returns a queryset of lectures for a specific section."""
        return Lecture.objects.filter(
            deleted_at__isnull=True, section=section
        ).order_by("order")

    @staticmethod
    def get_lectures_by_section_slug(slug):
        """Returns a queryset of lectures for a specific section slug."""
        return Lecture.objects.filter(
            deleted_at__isnull=True, section__slug=slug
        ).order_by("order")

    @staticmethod
    def get_lecture_by_slug(slug):
        """Returns a single lecture by slug."""
        return Lecture.objects.filter(slug=slug, deleted_at__isnull=True).first()

    @staticmethod
    def create_lecture(user, **validated_data):
        """Creates a new lecture."""
        return Lecture.objects.create(instructor=user, **validated_data)

    @staticmethod
    def save(lecture):
        """Saves a lecture instance."""
        lecture.save()
        return lecture
