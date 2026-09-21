from django.contrib.auth import get_user_model

User = get_user_model()


class UserRepository:
    """
    Repository to handle database interactions relating to the User model.
    """

    @staticmethod
    def get_user_by_id(user_id):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def get_user_by_email(email):
        return User.objects.filter(email=email).first()

    @staticmethod
    def get_all_users():
        """Returns a queryset of all users."""
        return User.objects.all()
