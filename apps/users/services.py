from django.core.cache import cache
from django.utils import timezone

from .cache import user_profile_cache_key


class UserService:
    """
    Service to handle business logic relating to the User model.
    """

    @staticmethod
    def make_instructor(user) -> str:
        """
        Grants a user the instructor role.
        """
        user.become_instructor()
        cache.delete(user_profile_cache_key(user.pk))
        return "User updated successfully"

    @staticmethod
    def toggle_admin(user) -> str:
        """
        Toggles admin privileges for a user.
        """
        action_taken = user.toggle_admin_privileges()
        cache.delete(user_profile_cache_key(user.pk))
        group_name = "admin"
        return f"User {action_taken} {group_name} group successfully"

    @staticmethod
    def toggle_status(user) -> str:
        """
        Activates or suspends a user's account.
        """
        action = user.toggle_status()
        cache.delete(user_profile_cache_key(user.pk))
        return f"User {action} successfully"

    @staticmethod
    def delete_user(user):
        """Soft-delete the account and disable authentication."""
        user.deleted_at = timezone.now()
        user.is_active = False
        user.status = user.Status.INACTIVE
        user.save(update_fields=["deleted_at", "is_active", "status", "updated_at"])
        cache.delete(user_profile_cache_key(user.pk))
