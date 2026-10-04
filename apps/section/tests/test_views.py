import pytest
from django.contrib.auth.models import Group

from apps.section.models import Section
from apps.section.tests.factories import SectionFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
PUBLIC = "/api/v1/section/"
MANAGE = PUBLIC + "instructor/all/"


def test_public_visibility_and_options(client, section):
    assert client.get(PUBLIC).data["count"] == 0
    section.status = "published"
    section.save()
    assert client.get(PUBLIC + f"{section.pk}/").status_code == 200
    assert client.options(PUBLIC).status_code == 200
    assert client.post(PUBLIC, {}).status_code == 405


def test_course_lookup(client, section):
    response = client.get(PUBLIC + f"course/{section.course.slug}/")
    assert response.status_code == 200
    assert response.data["results"][0]["id"] == str(section.pk)
    assert client.get(PUBLIC + "course/missing/").status_code == 404
    section.course.soft_delete()
    assert client.get(PUBLIC + f"course/{section.course.slug}/").status_code == 404


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_management_requires_auth(client, section, method):
    target = MANAGE if method in ("get", "post") else MANAGE + f"{section.pk}/"
    assert getattr(client, method)(target).status_code == 401


def test_create_update_delete(client, section, instructor):
    client.force_authenticate(instructor)
    response = client.post(
        MANAGE,
        {"title": "New", "description": "Intro", "course": str(section.course_id)},
        format="json",
    )
    assert response.status_code == 201, response.data
    created = Section.objects.get(pk=response.data["id"])
    assert created.instructor == instructor
    target = MANAGE + f"{created.pk}/"
    assert client.patch(target, {"title": "Updated"}, format="json").status_code == 200
    created.refresh_from_db()
    assert created.title == "Updated"
    assert client.delete(target).status_code == 204
    created.refresh_from_db()
    assert created.is_deleted


def test_foreign_hidden_student_denied(client, instructor):
    foreign = SectionFactory()
    client.force_authenticate(instructor)
    assert client.patch(MANAGE + f"{foreign.pk}/", {}).status_code == 404
    client.force_authenticate(UserFactory())
    assert client.get(MANAGE).status_code == 403


def test_admin_restore(client, section):
    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(admin)
    section.soft_delete()
    assert client.delete(MANAGE + f"{section.pk}/").status_code == 200
    section.refresh_from_db()
    assert not section.is_deleted


@pytest.mark.parametrize("endpoint", [PUBLIC, MANAGE, "course"])
@pytest.mark.parametrize(
    "parameter", ["search", "course", "course_slug", "instructor", "status"]
)
def test_section_search_and_filters(client, instructor, endpoint, parameter):
    matching = SectionFactory(
        course__instructor=instructor, title="Python basics", status="published"
    )
    other = SectionFactory(status="published", title="Java basics")
    if endpoint == MANAGE:
        client.force_authenticate(instructor)
        other.instructor = instructor
        other.save()
    elif endpoint == "course":
        endpoint = PUBLIC + f"course/{matching.course.slug}/"
    values = {
        "search": "pYtHoN",
        "course": str(matching.course_id),
        "course_slug": matching.course.slug.upper(),
        "instructor": str(instructor.pk),
        "status": "published",
    }
    if parameter == "status":
        other.status = "draft"
        other.save()
    response = client.get(endpoint, {parameter: values[parameter]})
    assert response.status_code == 200, response.data
    expected = [str(matching.pk)]
    if endpoint == MANAGE and parameter == "instructor":
        expected.append(str(other.pk))
    assert sorted(row["id"] for row in response.data["results"]) == sorted(expected)


@pytest.mark.parametrize("field", ["title", "description", "course"])
def test_section_search_fields(client, field):
    section = SectionFactory(status="published")
    if field == "course":
        section.course.title = "Unique search phrase"
        section.course.save()
    else:
        setattr(section, field, "Unique search phrase")
        section.save()
    SectionFactory(status="published")
    response = client.get(PUBLIC, {"search": "unique search"})
    assert [row["id"] for row in response.data["results"]] == [str(section.pk)]
    assert client.get(PUBLIC, {"search": "missing"}).data["count"] == 0


def test_combined_filters_and_course_scope(client, section):
    section.title = "Python"
    section.save()
    SectionFactory(course=section.course, title="Java")
    foreign = SectionFactory(title="Python")
    endpoint = PUBLIC + f"course/{section.course.slug}/"
    response = client.get(endpoint, {"search": "python", "status": "draft"})
    assert [row["id"] for row in response.data["results"]] == [str(section.pk)]
    assert client.get(endpoint, {"course": str(foreign.course_id)}).data["count"] == 0


def test_filters_preserve_section_visibility(client, instructor):
    visible = SectionFactory(status="published", course__instructor=instructor)
    SectionFactory(status="draft", course=visible.course)
    deleted = SectionFactory(status="published", course=visible.course)
    deleted.soft_delete()
    inactive = SectionFactory(status="published")
    inactive.instructor.status = "IA"
    inactive.instructor.save()
    response = client.get(PUBLIC, {"search": "Introduction"})
    assert [row["id"] for row in response.data["results"]] == [str(visible.pk)]
    assert client.get(PUBLIC, {"status": "draft"}).data["count"] == 0
    client.force_authenticate(instructor)
    response = client.get(MANAGE, {"instructor": str(inactive.instructor_id)})
    assert response.data["count"] == 0


@pytest.mark.parametrize("parameter", ["course", "instructor", "status"])
def test_invalid_section_filters(client, parameter):
    assert client.get(PUBLIC, {parameter: "invalid"}).status_code == 400


def test_section_ordering(client):
    later = SectionFactory(status="published", order=2, title="Alpha")
    earlier = SectionFactory(status="published", order=1, title="Beta")
    response = client.get(PUBLIC)
    assert [row["id"] for row in response.data["results"]] == [
        str(earlier.pk),
        str(later.pk),
    ]
    for ordering in ("-order", "title"):
        response = client.get(PUBLIC, {"ordering": ordering})
        assert [row["id"] for row in response.data["results"]] == [
            str(later.pk),
            str(earlier.pk),
        ]
