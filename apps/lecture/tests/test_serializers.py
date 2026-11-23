import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import serializers

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


@override_settings(MAX_LECTURE_VIDEO_SIZE=4)
def test_source_rejects_files_over_configured_size():
    serializer = LectureSerializer()
    upload = SimpleUploadedFile("lecture.mp4", b"12345", content_type="video/mp4")

    with pytest.raises(serializers.ValidationError, match="maximum upload size"):
        serializer.validate_source(upload)


@override_settings(MAX_LECTURE_VIDEO_SIZE=4)
def test_source_accepts_files_at_configured_size():
    serializer = LectureSerializer()
    upload = SimpleUploadedFile("lecture.mp4", b"1234", content_type="video/mp4")

    assert serializer.validate_source(upload) is upload
