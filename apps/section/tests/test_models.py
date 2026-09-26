import pytest

from apps.section.tests.factories import SectionFactory

pytestmark = pytest.mark.django_db


def test_generated_slug_is_stable():
    obj = SectionFactory(title="Python Basics", slug=None)
    assert obj.slug.startswith("python-basics-")
    slug = obj.slug
    obj.title = "Updated"
    obj.save()
    obj.refresh_from_db()
    assert obj.slug == slug
    assert str(obj) == "Updated"


def test_custom_slug():
    assert SectionFactory(slug="custom").slug == "custom"


def test_soft_delete_restore_and_toggle(section):
    section.soft_delete()
    section.refresh_from_db()
    assert section.is_deleted
    section.restore()
    section.refresh_from_db()
    assert not section.is_deleted
    section.toggle_deleted()
    section.refresh_from_db()
    assert section.is_deleted
    section.toggle_deleted()
    section.refresh_from_db()
    assert not section.is_deleted
