from .models import Rating


class RatingRepository:
    """
    Repository to handle database interactions relating to the Rating model.
    """

    @staticmethod
    def get_all_ratings():
        """Returns a queryset of all ratings."""
        return Rating.objects.filter(deleted_at__isnull=True).order_by("-created_at")

    @staticmethod
    def get_instructor_ratings(user):
        """Returns a queryset of ratings for courses belonging to the instructor."""
        return Rating.objects.filter(
            deleted_at__isnull=True, course__instructor=user
        ).order_by("-created_at")

    @staticmethod
    def get_course_ratings(course_id):
        """Returns ratings for a specific course."""
        return Rating.objects.filter(
            deleted_at__isnull=True, course_id=course_id
        ).order_by("-created_at")

    @staticmethod
    def create_rating(user, **validated_data):
        """Creates a new rating."""
        return Rating.objects.create(user=user, **validated_data)

    @staticmethod
    def save(rating):
        """Saves a rating instance."""
        rating.save()
        return rating
