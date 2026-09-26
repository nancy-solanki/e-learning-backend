import pytest

from apps.lecture.tests.factories import LectureFactory

pytestmark = pytest.mark.django_db


def test_generated_slug_is_stable():
    obj = LectureFactory(title="Python Basics", slug=None)
    assert obj.slug.startswith("python-basics-")
    slug = obj.slug
    obj.title = "Updated"
    obj.save()
    obj.refresh_from_db()
    assert obj.slug == slug
    assert str(obj) == "Updated"


def test_custom_slug():
    assert LectureFactory(slug="custom").slug == "custom"


def test_soft_delete_restore_and_toggle(lecture):
    lecture.soft_delete()
    lecture.refresh_from_db()
    assert lecture.is_deleted
    lecture.restore()
    lecture.refresh_from_db()
    assert not lecture.is_deleted
    lecture.toggle_deleted()
    lecture.refresh_from_db()
    assert lecture.is_deleted
    lecture.toggle_deleted()
    lecture.refresh_from_db()
    assert not lecture.is_deleted
