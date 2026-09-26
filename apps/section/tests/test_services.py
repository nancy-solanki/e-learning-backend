import pytest

from apps.section.service import SectionService

pytestmark = pytest.mark.django_db


def test_queries_and_lifecycle(section, instructor):
    section.status = "published"
    section.save()
    assert list(SectionService.get_public_queryset()) == [section]
    assert list(SectionService.get_queryset_for_user(instructor)) == [section]
    assert list(SectionService.get_sections_by_course(section.course)) == [section]
    SectionService.delete_section(section)
    section.refresh_from_db()
    assert section.is_deleted
    SectionService.restore_section(section)
    section.refresh_from_db()
    assert not section.is_deleted
    assert SectionService.toggle_section_status(section) == "deleted"
