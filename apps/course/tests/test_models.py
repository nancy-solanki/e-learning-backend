import pytest

from apps.course.tests.factories import CourseFactory

pytestmark = pytest.mark.django_db


def test_generated_slug_is_stable():
    obj = CourseFactory(title="Python Basics", slug=None)
    assert obj.slug.startswith("python-basics-")
    slug = obj.slug
    obj.title = "Updated"
    obj.save()
    obj.refresh_from_db()
    assert obj.slug == slug
    assert str(obj) == "Updated"


def test_custom_slug():
    assert CourseFactory(slug="custom").slug == "custom"


def test_soft_delete_restore_and_toggle(course):
    course.soft_delete()
    course.refresh_from_db()
    assert course.is_deleted
    course.restore()
    course.refresh_from_db()
    assert not course.is_deleted
    course.toggle_deleted()
    course.refresh_from_db()
    assert course.is_deleted
    course.toggle_deleted()
    course.refresh_from_db()
    assert not course.is_deleted
