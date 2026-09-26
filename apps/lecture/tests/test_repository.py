import pytest
from django.utils import timezone

from apps.lecture.repository import LectureRepository
from apps.lecture.tests.factories import LectureFactory

pytestmark = pytest.mark.django_db


def test_visibility_and_scoping(lecture, instructor):
    lecture.status = "published"
    lecture.order = 2
    lecture.save()
    first = LectureFactory(section=lecture.section, status="published", order=1)
    draft = LectureFactory(section=lecture.section)
    deleted = LectureFactory(section=lecture.section, deleted_at=timezone.now())
    inactive = LectureFactory(
        status="published", section__course__instructor__status="SA"
    )
    assert list(LectureRepository.get_active_lectures()) == [first, lecture]
    assert set(LectureRepository.get_instructor_lectures(instructor)) == {
        first,
        lecture,
        draft,
    }
    assert set(LectureRepository.get_all_lectures()) == {
        first,
        lecture,
        draft,
        inactive,
    }
    assert deleted in LectureRepository.get_admin_lectures()
    assert set(LectureRepository.get_lectures_by_section(lecture.section)) == {
        first,
        lecture,
        draft,
    }
    assert set(
        LectureRepository.get_lectures_by_section_slug(lecture.section.slug)
    ) == {first, lecture, draft}
    assert LectureRepository.get_lecture_by_slug(lecture.slug) == lecture
    assert LectureRepository.get_lecture_by_slug(deleted.slug) is None
    assert LectureRepository.get_lecture_by_slug("missing") is None


def test_save(lecture):
    lecture.title = "Updated"
    assert LectureRepository.save(lecture) == lecture
    lecture.refresh_from_db()
    assert lecture.title == "Updated"
