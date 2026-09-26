import pytest
from django.contrib.auth.models import Group

from apps.lecture.models import Lecture
from apps.lecture.tests.factories import LectureFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
PUBLIC = "/api/v1/lecture/"
MANAGE = PUBLIC + "instructor/all/"


def test_public_visibility_and_options(client, lecture):
    assert client.get(PUBLIC).data["count"] == 0
    lecture.status = "published"
    lecture.save()
    assert client.get(PUBLIC + f"{lecture.pk}/").status_code == 200
    assert client.options(PUBLIC).status_code == 200
    assert client.post(PUBLIC, {}).status_code == 405


def test_section_lookup(client, lecture):
    response = client.get(PUBLIC + f"section/{lecture.section.slug}/")
    assert response.status_code == 200
    assert response.data[0]["id"] == str(lecture.pk)
    assert client.get(PUBLIC + "section/missing/").status_code == 404


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_management_requires_auth(client, lecture, method):
    target = MANAGE if method in ("get", "post") else MANAGE + f"{lecture.pk}/"
    assert getattr(client, method)(target).status_code == 401


def test_create_returns_saved_object_update_and_delete(client, lecture, instructor):
    client.force_authenticate(instructor)
    data = {
        "title": "New",
        "description": "Intro",
        "course": str(lecture.course_id),
        "section": str(lecture.section_id),
        "lecture_type": "document",
        "document_content": "Content",
        "duration": "10:00",
    }
    response = client.post(MANAGE, data, format="json")
    assert response.status_code == 201, response.data
    created = Lecture.objects.get(pk=response.data["id"])
    assert response.data["instructor"] == instructor.username
    assert created.instructor == instructor
    target = MANAGE + f"{created.pk}/"
    assert client.patch(target, {"title": "Updated"}, format="json").status_code == 200
    created.refresh_from_db()
    assert created.title == "Updated"
    assert client.delete(target).status_code == 200
    created.refresh_from_db()
    assert created.is_deleted


def test_foreign_hidden_and_student_denied(client, instructor):
    foreign = LectureFactory()
    client.force_authenticate(instructor)
    assert client.patch(MANAGE + f"{foreign.pk}/", {}).status_code == 404
    client.force_authenticate(UserFactory())
    assert client.get(MANAGE).status_code == 403


def test_admin_restore(client, lecture):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(user)
    lecture.soft_delete()
    assert client.delete(MANAGE + f"{lecture.pk}/").status_code == 200
    lecture.refresh_from_db()
    assert not lecture.is_deleted
