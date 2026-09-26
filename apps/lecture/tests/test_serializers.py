import pytest

from apps.lecture.serializers import LectureSerializer
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", ""),
        ("title", "x" * 251),
        ("status", "invalid"),
        ("lecture_type", "invalid"),
        ("order", "bad"),
    ],
)
def test_invalid_update(lecture, field, value):
    serializer = LectureSerializer(lecture, data={field: value}, partial=True)
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_representation_and_readonly_instructor(lecture):
    serializer = LectureSerializer(
        lecture, data={"instructor": str(UserFactory().pk)}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    assert "instructor" not in serializer.validated_data
    assert serializer.data["instructor"] == lecture.instructor.username
