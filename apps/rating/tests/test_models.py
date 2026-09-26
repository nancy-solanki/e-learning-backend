import pytest

pytestmark = pytest.mark.django_db


def test_string(rating):
    assert str(rating) == f"{rating.user} - {rating.course.title} ({rating.rating})"


def test_soft_delete_and_restore(rating):
    rating.soft_delete()
    rating.refresh_from_db()
    assert rating.is_deleted
    rating.restore()
    rating.refresh_from_db()
    assert not rating.is_deleted
