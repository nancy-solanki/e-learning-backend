import pytest

from apps.enroll.models import Enroll
from apps.enroll.service import EnrollService

pytestmark = pytest.mark.django_db


def test_enrollment_idempotency(enroll):
    assert (
        EnrollService.enroll_user_in_course(enroll.user, enroll.course)
        == "Already enrolled"
    )
    assert Enroll.objects.count() == 1
    enroll.soft_delete()
    assert (
        EnrollService.enroll_user_in_course(enroll.user, enroll.course)
        == "Successfully enrolled"
    )
    assert Enroll.objects.filter(deleted_at__isnull=True).count() == 1


def test_role_scoping(enroll):
    instructor = enroll.course.instructor
    instructor.become_instructor()
    assert list(EnrollService.get_enrollments(instructor)) == [enroll]
    assert list(EnrollService.get_enrollments(enroll.user)) == [enroll]
    enroll.course.status = "published"
    enroll.course.save()
    assert list(EnrollService.get_enrollments_by_course(enroll.course.slug)) == [enroll]
