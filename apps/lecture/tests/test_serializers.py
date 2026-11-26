import pytest
from django.test import override_settings

from apps.lecture.serializers import LectureSerializer
from apps.lecture.upload_views import InitiateUploadSerializer
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


def test_source_accepts_private_s3_key(lecture):
    key = f"source/{lecture.instructor_id}/upload-token/lecture.mp4"
    serializer = LectureSerializer(lecture, data={"source": key}, partial=True)

    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["source"] == key


@override_settings(MAX_LECTURE_VIDEO_SIZE=4)
def test_video_upload_size_is_validated_when_initiated():
    serializer = InitiateUploadSerializer(
        data={
            "filename": "lecture.mp4",
            "content_type": "video/mp4",
            "size": 5,
        }
    )

    assert not serializer.is_valid()
    assert "size" in serializer.errors


@override_settings(MAX_LECTURE_RESOURCE_SIZE=4)
def test_arbitrary_resource_content_type_and_size_limit():
    serializer = InitiateUploadSerializer(
        data={
            "filename": "handout.zip",
            "content_type": "application/zip",
            "kind": "resource",
            "size": 4,
        }
    )

    assert serializer.is_valid(), serializer.errors
