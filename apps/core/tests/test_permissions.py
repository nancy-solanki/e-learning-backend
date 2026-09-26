from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, Group

from apps.core.permission import (
    IsInstructorOrAdmin,
    IsInstructorOrReadOnly,
    IsOwnerOrInstructor,
    IsOwnerOrReadOnly,
    IsSuperuser,
    IsSuperuserOrReadOnly,
)
from apps.users.tests.factories import SuperuserFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def role_user():
    def create(role):
        if role == "anonymous":
            return AnonymousUser()
        user = SuperuserFactory() if role == "superuser" else UserFactory()
        if role in ("admin", "instructor"):
            user.groups.add(Group.objects.get_or_create(name=role)[0])
        return user

    return create


@pytest.mark.parametrize(
    "role", ["anonymous", "student", "instructor", "admin", "superuser"]
)
@pytest.mark.parametrize(
    "method", ["GET", "HEAD", "OPTIONS", "POST", "PATCH", "DELETE"]
)
def test_request_permission_matrix(role_user, role, method):
    request = SimpleNamespace(user=role_user(role), method=method)
    safe = method in ("GET", "HEAD", "OPTIONS")
    admin = role in ("admin", "superuser")
    assert bool(IsSuperuser().has_permission(request, None)) == admin
    assert bool(IsSuperuserOrReadOnly().has_permission(request, None)) == (
        safe or admin
    )
    assert bool(IsInstructorOrReadOnly().has_permission(request, None)) == (
        safe or role == "instructor"
    )
    expected = role == "instructor" or (method != "POST" and role == "admin")
    assert bool(IsInstructorOrAdmin().has_permission(request, None)) == expected
    for permission in (IsOwnerOrReadOnly(), IsOwnerOrInstructor()):
        assert bool(permission.has_permission(request, None)) == (role != "anonymous")


@pytest.mark.parametrize(
    "relation", ["owner", "instructor", "course_instructor", "stranger", "admin"]
)
@pytest.mark.parametrize("method", ["GET", "PATCH"])
def test_object_permission_matrix(role_user, relation, method):
    owner = role_user("instructor")
    instructor = role_user("instructor")
    course_instructor = role_user("instructor")
    user = {
        "owner": owner,
        "instructor": instructor,
        "course_instructor": course_instructor,
        "stranger": role_user("student"),
        "admin": role_user("admin"),
    }[relation]
    obj = SimpleNamespace(user=owner, instructor=instructor)
    # Exercise instructor resolution through related course separately.
    if relation == "course_instructor":
        obj.instructor = None
        obj.course = SimpleNamespace(instructor=course_instructor)
    request = SimpleNamespace(user=user, method=method)
    safe = method == "GET"
    assert bool(IsOwnerOrReadOnly().has_object_permission(request, None, obj)) == (
        safe or relation in ("owner", "admin")
    )
    assert bool(IsInstructorOrReadOnly().has_object_permission(request, None, obj)) == (
        safe or relation != "stranger"
    )
    assert bool(IsOwnerOrInstructor().has_object_permission(request, None, obj)) == (
        safe or relation != "stranger"
    )
    assert bool(IsInstructorOrAdmin().has_object_permission(request, None, obj)) == (
        relation in ("instructor", "admin")
    )


def test_non_instructor_bank_owner_cannot_write(role_user):
    user = role_user("student")
    request = SimpleNamespace(user=user, method="PATCH")
    assert not IsInstructorOrReadOnly().has_object_permission(
        request, None, SimpleNamespace(user=user)
    )


def test_instructor_permission_handles_missing_user():
    assert not IsInstructorOrAdmin().has_permission(
        SimpleNamespace(method="POST"), None
    )
