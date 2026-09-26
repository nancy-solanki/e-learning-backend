import pytest
from django.contrib.auth.models import Group

from apps.users.serializers import UserProfileSerializer, UserSerializer
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", ["student", "instructor", "admin"])
def test_profile_roles_and_sensitive_fields(role):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name=role)[0])
    data = UserProfileSerializer(user).data
    if role == "student":
        assert "role" not in data
    else:
        assert data["role"] == [role]
    assert "password" not in data
    assert "is_superuser" not in data
    assert data["gender"] == "MALE"


def test_user_representation():
    user = UserFactory()
    data = UserSerializer(user).data
    assert data["id"] == str(user.pk)
    assert data["status"] == "ACTIVE"
    assert "password" not in data


@pytest.mark.parametrize(
    "field, value",
    [
        ("email", "invalid"),
        ("avatar", "invalid"),
        ("phone_number", "1" * 16),
        ("birth_date", "invalid"),
        ("first_name", "x" * 201),
    ],
)
def test_profile_validation(user, field, value):
    serializer = UserProfileSerializer(user, data={field: value}, partial=True)
    assert not serializer.is_valid()
    assert field in serializer.errors


@pytest.mark.parametrize("field", ["email", "username"])
def test_duplicate_profile_fields(user, field):
    other = UserFactory()
    serializer = UserProfileSerializer(
        user, data={field: getattr(other, field)}, partial=True
    )
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_profile_cannot_elevate_privileges(user):
    serializer = UserProfileSerializer(
        user,
        data={
            "is_superuser": True,
            "is_staff": True,
            "role": ["admin"],
            "status": "SA",
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    user.refresh_from_db()
    assert not user.is_superuser
    assert not user.is_staff
    assert not user.is_admin
    assert user.status == "AC"
