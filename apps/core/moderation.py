"""Admin moderation rules for courses, sections, and lectures."""

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .permission import IsInstructorOrAdmin


class IsInstructorOrContentAdmin(IsInstructorOrAdmin):
    def has_permission(self, request, view):
        if getattr(request.user, "is_admin", False):
            return request.method != "POST"
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if getattr(request.user, "is_admin", False):
            return True
        return super().has_object_permission(request, view, obj)


class AdminStatusOnlyMixin:
    """Admins may update only status and delete without restoring content."""

    admin_delete_status = status.HTTP_204_NO_CONTENT

    def update(self, request, *args, **kwargs):
        if request.user.is_admin:
            if set(request.data) - {"status"}:
                raise PermissionDenied("Admins may only update status.")
            # PUT must not require the metadata that admins cannot edit.
            kwargs["partial"] = True
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return self._destroy_instructor(request, *args, **kwargs)
        instance = self.get_object()
        if not instance.is_deleted:
            instance.soft_delete()
        if self.admin_delete_status == status.HTTP_204_NO_CONTENT:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"message": "Lecture deleted successfully"},
            status=self.admin_delete_status,
        )
