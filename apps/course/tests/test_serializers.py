import pytest

from apps.category.tests.factories import CategoryFactory
from apps.course.models import Tag
from apps.course.serializers import (
    CourseMinimalSerializer,
    CourseSerializer,
    FilteredCourseSerializer,
    TagSerializer,
)
from apps.enroll.models import Enroll
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_nested_representation_with_avatar(course):
    course.instructor.avatar = "https://example.com/avatar.png"
    course.instructor.save()
    category = CategoryFactory()
    course.categories.add(category)
    tag = Tag.objects.create(name="Python Basics")
    course.tags.add(tag)
    Enroll.objects.create(user=UserFactory(), course=course)
    data = FilteredCourseSerializer(course).data
    assert data["instructor"]["avatar"] == course.instructor.avatar
    assert data["thumbnail"]["url"] == course.thumbnail.url
    assert data["categories"][0]["id"] == str(category.pk)
    assert data["tags"][0]["slug"] == "python-basics"
    assert data["student_count"] == 1
    assert CourseSerializer(course).data["student_count"] == 1
    assert (
        CourseMinimalSerializer(course).data["instructor"]["avatar"]
        == course.instructor.avatar
    )
    assert str(tag) == "Python Basics"
    assert TagSerializer(tag).data["slug"] == "python-basics"


@pytest.mark.parametrize(
    "field,value",
    [("title", ""), ("title", "x" * 251), ("status", "invalid"), ("price", "bad")],
)
def test_invalid_update(course, field, value):
    serializer = CourseSerializer(course, data={field: value}, partial=True)
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_instructor_is_read_only(course):
    serializer = CourseSerializer(
        course, data={"instructor": str(UserFactory().pk)}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    assert "instructor" not in serializer.validated_data
