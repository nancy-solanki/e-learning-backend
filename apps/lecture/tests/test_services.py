import pytest

from apps.lecture.models import Lecture
from apps.lecture.service import LectureService

pytestmark = pytest.mark.django_db


def test_create_document_and_input_unchanged(lecture, instructor):
    data = {
        "title": "Document",
        "course": lecture.course,
        "section": lecture.section,
        "lecture_type": "document",
        "document_content": "Content",
        "duration": "99:99",
    }
    created = LectureService.create_lecture(instructor, data)
    created.refresh_from_db()
    assert created.instructor == instructor
    assert created.duration is None
    assert created.document_content == "Content"
    assert data["duration"] == "99:99"


@pytest.mark.parametrize("fails", [False, True])
def test_video_processing_closes_clip_and_handles_failure(
    lecture, instructor, mocker, fails
):
    source = mocker.Mock()
    source.temporary_file_path.return_value = "/tmp/test-video.mp4"
    video = mocker.patch("apps.lecture.service.VideoFileClip")
    video.return_value.__enter__.return_value.duration = 125.8
    if fails:
        video.side_effect = RuntimeError("Invalid video")
    # Persistence is isolated here to avoid uploading the synthetic video to cloud storage.
    create = mocker.patch(
        "apps.lecture.service.LectureRepository.create_lecture", return_value=lecture
    )
    result = LectureService.create_lecture(instructor, {"source": source})
    assert result == lecture
    assert create.call_args.kwargs["duration"] == (None if fails else "02:05")
    if not fails:
        video.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize(
    "hours, expected",
    [("01:30", "01:32:00"), ("01:30:00", "01:32:00"), ("invalid", "invalid")],
)
def test_publication_updates_course_and_section(lecture, hours, expected):
    lecture.course.total_hours = hours
    lecture.course.save()
    LectureService._handle_publication(lecture, 2)
    lecture.course.refresh_from_db()
    lecture.section.refresh_from_db()
    assert lecture.course.total_hours == expected
    assert lecture.section.status == "published"


def test_published_creation_updates_section(lecture, instructor):
    result = LectureService.create_lecture(
        instructor,
        {
            "title": "Published",
            "course": lecture.course,
            "section": lecture.section,
            "status": "published",
            "lecture_type": "document",
        },
    )
    assert Lecture.objects.filter(pk=result.pk).exists()
    lecture.section.refresh_from_db()
    assert lecture.section.status == "published"


def test_toggle_status(lecture):
    assert (
        LectureService.toggle_lecture_status(lecture) == "Lecture deleted successfully"
    )
    lecture.refresh_from_db()
    assert lecture.is_deleted
    assert (
        LectureService.toggle_lecture_status(lecture)
        == "Lecture activated successfully"
    )
    lecture.refresh_from_db()
    assert not lecture.is_deleted
