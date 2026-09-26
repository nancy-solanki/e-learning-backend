import pytest
from django.utils import timezone

from apps.enroll.repository import EnrollRepository
from apps.enroll.tests.factories import EnrollFactory

pytestmark = pytest.mark.django_db


def test_scoping_and_visibility(enroll):
    foreign = EnrollFactory()
    EnrollFactory(user=enroll.user, course=enroll.course, deleted_at=timezone.now())
    assert set(EnrollRepository.get_all_enrollments()) == {enroll, foreign}
    assert list(EnrollRepository.get_user_enrollments(enroll.user)) == [enroll]
    assert list(
        EnrollRepository.get_instructor_enrollments(enroll.course.instructor)
    ) == [enroll]
    assert list(EnrollRepository.get_enrollments_by_course(enroll.course)) == [enroll]
    assert not EnrollRepository.get_enrollments_by_course_slug(
        enroll.course.slug
    ).exists()
    enroll.course.status = "published"
    enroll.course.save()
    assert list(
        EnrollRepository.get_enrollments_by_course_slug(enroll.course.slug)
    ) == [enroll]


def test_create_delete(enroll):
    created = EnrollRepository.create_enrollment(enroll.user, enroll.course)
    assert created.pk != enroll.pk
    EnrollRepository.delete_enrollment(created)
    created.refresh_from_db()
    assert created.is_deleted
