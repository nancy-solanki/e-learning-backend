import pytest

from apps.section.serializers import FilteredSectionSerializer, SectionSerializer

pytestmark = pytest.mark.django_db


def test_representation(section):
    assert SectionSerializer(section).data["course_title"] == section.course.title
    assert (
        FilteredSectionSerializer(section).data["instructor"]
        == section.instructor.username
    )


@pytest.mark.parametrize(
    "field,value",
    [("title", ""), ("title", "x" * 251), ("status", "invalid"), ("order", "bad")],
)
def test_invalid_update(section, field, value):
    serializer = SectionSerializer(section, data={field: value}, partial=True)
    assert not serializer.is_valid()
    assert field in serializer.errors
