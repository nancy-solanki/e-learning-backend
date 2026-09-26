import pytest
from django.utils import timezone

from apps.section.repository import SectionRepository
from apps.section.tests.factories import SectionFactory
from apps.users.tests.factories import SuperuserFactory

pytestmark = pytest.mark.django_db


def test_visibility_and_order(section, instructor):
    section.status = "published"
    section.order = 2
    section.save()
    first = SectionFactory(course=section.course, status="published", order=1)
    draft = SectionFactory(course=section.course)
    deleted = SectionFactory(course=section.course, deleted_at=timezone.now())
    SectionFactory(status="published", course__instructor__status="SA")
    assert list(SectionRepository.get_all_published_sections()) == [first, section]
    assert set(SectionRepository.get_sections_by_course(section.course)) == {
        first,
        section,
        draft,
    }
    assert list(SectionRepository.get_published_sections_by_course(section.course)) == [
        first,
        section,
    ]
    assert set(SectionRepository.get_user_sections(instructor)) == {
        first,
        section,
        draft,
    }
    assert deleted in SectionRepository.get_user_sections(SuperuserFactory())
    assert SectionRepository.get_section_by_slug(section.slug) == section
    assert SectionRepository.get_section_by_slug("missing") is None


def test_create_and_update(section):
    created = SectionRepository.create_section(
        title="New",
        description="Intro",
        course=section.course,
        instructor=section.instructor,
    )
    assert SectionRepository.update_section(created, title="Updated") == created
    created.refresh_from_db()
    assert created.title == "Updated"
