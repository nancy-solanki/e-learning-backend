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
    assert response.data[0]["id"] == str(section.pk)
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
