from .repository import RatingRepository


class RatingService:
    """
    Service to handle business logic relating to the Rating model.
    """

    @staticmethod
    def get_ratings(user):
        """Returns ratings based on user role."""
        if user.is_instructor:
            return RatingRepository.get_instructor_ratings(user)
        return RatingRepository.get_all_ratings()

    @staticmethod
    def add_rating(user, validated_data):
        """Logic for adding a rating, potentially checking if already rated."""
        # Add checks if necessary (e.g. only one rating per course per user)
        return RatingRepository.create_rating(user, **validated_data)

    @staticmethod
    def get_instructor_course_ratings(user):
        """Returns ratings for courses where user is the instructor."""
        return RatingRepository.get_instructor_ratings(user)
