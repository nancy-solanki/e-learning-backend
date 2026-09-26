import pytest

pytestmark = pytest.mark.django_db


def test_soft_delete_and_restore(enroll):
    enroll.soft_delete()
    enroll.refresh_from_db()
    assert enroll.is_deleted
    enroll.restore()
    enroll.refresh_from_db()
    assert not enroll.is_deleted


def test_string(enroll):
    assert str(enroll) == f"{enroll.user} - {enroll.course.title}"
