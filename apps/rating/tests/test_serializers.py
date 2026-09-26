from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.course.tests.factories import CourseFactory
from apps.enroll.models import Enroll
from apps.rating.serializers import RatingSerializer
from apps.rating.tests.factories import RatingFactory
from apps.users.tests.factories import SuperuserFactory, UserFactory

pytestmark = pytest.mark.django_db


def serializer_for(user, data, instance=None):
    return RatingSerializer(
        instance,
        data=data,
        partial=instance is not None,
        context={"request": SimpleNamespace(user=user)},
    )


@pytest.mark.parametrize(
    "enrolled, deleted, valid",
    [(False, False, False), (True, True, False), (True, False, True)],
)
def test_enrollment_required(course, enrolled, deleted, valid):
    user = UserFactory()
    if enrolled:
        Enroll.objects.create(
            user=user, course=course, deleted_at=timezone.now() if deleted else None
        )
    serializer = serializer_for(
        user, {"course": str(course.pk), "rating": "4.0", "comment": "Good"}
    )
    assert serializer.is_valid() is valid


def test_duplicate_rating_rejected(rating):
    Enroll.objects.create(user=rating.user, course=rating.course)
    serializer = serializer_for(
        rating.user, {"course": str(rating.course_id), "rating": 4, "comment": "Again"}
    )
    assert not serializer.is_valid()
    assert "already rated" in str(serializer.errors)


def test_deleted_rating_can_be_replaced(course):
    user = UserFactory()
    Enroll.objects.create(user=user, course=course)
    RatingFactory(user=user, course=course, deleted_at=timezone.now())
    serializer = serializer_for(
        user,
        {
            "course": str(course.pk),
            "rating": 4,
            "comment": "Good",
            "response": "Fake reply",
        },
    )
    assert serializer.is_valid(), serializer.errors
    assert "response" not in serializer.validated_data


@pytest.mark.parametrize(
    "role, data, valid",
    [
        ("owner", {"comment": "Updated"}, True),
        ("owner", {"response": "Reply"}, False),
        ("instructor", {"response": "Thanks"}, True),
        ("instructor", {"rating": 5}, False),
        ("instructor", {"comment": "Changed"}, False),
        ("stranger", {"comment": "Changed"}, False),
        ("admin", {"comment": "Moderated"}, True),
    ],
)
def test_update_roles(rating, role, data, valid):
    user = {
        "owner": rating.user,
        "instructor": rating.course.instructor,
        "stranger": UserFactory(),
        "admin": SuperuserFactory(),
    }[role]
    serializer = serializer_for(user, data, rating)
    assert serializer.is_valid() is valid


@pytest.mark.parametrize("role", ["owner", "instructor"])
def test_course_cannot_be_reassigned(rating, role):
    user = rating.user if role == "owner" else rating.course.instructor
    serializer = serializer_for(user, {"course": str(CourseFactory().pk)}, rating)
    assert serializer.is_valid(), serializer.errors
    assert "course" not in serializer.validated_data


@pytest.mark.parametrize(
    "field, value",
    [
        ("rating", "invalid"),
        ("rating", "4.55"),
        ("comment", ""),
        ("comment", "x" * 5001),
    ],
)
def test_invalid_fields(rating, field, value):
    serializer = serializer_for(rating.user, {field: value}, rating)
    assert not serializer.is_valid()
    assert field in serializer.errors
