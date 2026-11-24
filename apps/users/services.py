from django.core.cache import cache
from django.utils import timezone

from apps.core.email_notifications import queue_notification_email

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
        queue_notification_email(
            user,
            subject="Instructor access enabled",
            title="Your instructor account is ready",
            message="Instructor access has been enabled for your Learnify account.",
            preference_required=False,
        )
        return "User updated successfully"

    @staticmethod
    def toggle_admin(user) -> str:
        """
        Toggles admin privileges for a user.
        """
        action_taken = user.toggle_admin_privileges()
        cache.delete(user_profile_cache_key(user.pk))
        group_name = "admin"
        added = action_taken == "added to"
        queue_notification_email(
            user,
            subject="Administrator access updated",
            title=(
                "Administrator access enabled"
                if added
                else "Administrator access removed"
            ),
            message=(
                "Administrator access has been enabled for your Learnify account."
                if added
                else "Administrator access has been removed from your Learnify account."
            ),
            preference_required=False,
        )
        return f"User {action_taken} {group_name} group successfully"

    @staticmethod
    def toggle_instructor(user) -> str:
        action_taken = user.toggle_instructor_privileges()
        cache.delete(user_profile_cache_key(user.pk))
        added = action_taken == "added to"
        queue_notification_email(
            user,
            subject="Instructor access updated",
            title=(
                "Instructor access enabled" if added else "Instructor access removed"
            ),
            message=(
                "Instructor access has been enabled for your Learnify account."
                if added
                else "Instructor access has been removed from your Learnify account."
            ),
            preference_required=False,
        )
        return f"User {action_taken} instructor group successfully"

    @staticmethod
    def toggle_status(user, reason: str = "") -> str:
        """
        Activates or suspends a user's account.
        """
        action = user.toggle_status(reason=reason)
        cache.delete(user_profile_cache_key(user.pk))
        suspended = action == "suspended"
        reason_text = f" Reason: {reason.strip()}" if reason.strip() else ""
        queue_notification_email(
            user,
            subject=(
                "Your Learnify account has been suspended"
                if suspended
                else "Your Learnify account is active again"
            ),
            title="Account suspended" if suspended else "Account reactivated",
            message=(
                "Your Learnify account has been suspended by an administrator. "
                "Contact support if you believe this is a mistake."
                f"{reason_text}"
                if suspended
                else "Your Learnify account has been reactivated and you can sign in again."
            ),
            preference_required=False,
        )
        return f"User {action} successfully"

    @staticmethod
    def delete_user(user):
        """Soft-delete the account and disable authentication."""
        user.deleted_at = timezone.now()
        user.is_active = False
        user.status = user.Status.INACTIVE
        user.save(update_fields=["deleted_at", "is_active", "status", "updated_at"])
        cache.delete(user_profile_cache_key(user.pk))
        queue_notification_email(
            user,
            subject="Your Learnify account was deactivated",
            title="Account deactivated",
            message=(
                "Your account has been deactivated and sign-in is disabled. Your "
                "existing enrollments, courses, and purchase records remain in "
                "Learnify's records. Contact support if you need help."
            ),
            preference_required=False,
        )
