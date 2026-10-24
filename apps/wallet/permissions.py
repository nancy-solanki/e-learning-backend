from rest_framework.permissions import BasePermission


class IsWalletUser(BasePermission):
    """Wallet readers must be admins or instructors; queries enforce ownership."""

    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (
            user.is_superuser
            or user.groups.filter(name__in=["admin", "instructor"]).exists()
        )
