from rest_framework import permissions


class IsSuperuser(permissions.BasePermission):
    """
    Custom permission to only allow superuser to perform actions.
    """

    def has_permission(self, request, view):
        """
        Check if user is a superuser
        """
        return request.user.is_authenticated and (
            request.user.is_superuser
            or request.user.groups.filter(name="admin").exists()
        )


class IsSuperuserOrReadOnly(IsSuperuser):
    """
    Custom permission that grants full access to superusers,
    but only read-only access (safe methods) to others.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_permission(request, view)


class IsInstructorOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow instructors or admins to perform actions.
    """

    def has_permission(self, request, view):
        try:
            if request.method == "POST":
                return request.user.groups.filter(name="instructor").exists()
            return (
                request.user.groups.filter(name="instructor").exists()
                or request.user.groups.filter(name="admin").exists()
            )
        except (AttributeError, TypeError):
            return False

    def has_object_permission(self, request, view, obj):
        return (
            request.user == obj.instructor
            or request.user.groups.filter(name="admin").exists()
        )


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow instructors to manage their resources.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="instructor").exists()
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instructor of the course or object
        instructor = getattr(obj, "instructor", None)
        if not instructor and hasattr(obj, "course"):
            instructor = getattr(obj.course, "instructor", None)

        # If the object is a Bank, the owner is a user who is an instructor
        user_owner = getattr(obj, "user", None)
        is_instructor_user = False
        if user_owner and user_owner.groups.filter(name="instructor").exists():
            is_instructor_user = request.user == user_owner

        return (
            request.user == instructor
            or is_instructor_user
            or request.user.groups.filter(name="admin").exists()
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow owners (students/users) to create/modify their resources.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user == obj.user
            or request.user.groups.filter(name="admin").exists()
        )


class IsOwnerOrInstructor(permissions.BasePermission):
    """
    Permission to allow either the resource owner (student) or the
    course/resource instructor to modify.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return IsOwnerOrReadOnly().has_object_permission(
            request, view, obj
        ) or IsInstructorOrReadOnly().has_object_permission(request, view, obj)
