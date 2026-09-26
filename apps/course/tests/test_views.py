import pytest
from django.contrib.auth.models import Group

from apps.category.tests.factories import CategoryFactory
from apps.common.tests.factories import FileFactory
from apps.course.models import Course
from apps.course.tests.factories import CourseFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
PUBLIC = "/api/v1/course/"
MANAGE = PUBLIC + "instructor/all/"


def test_public_list_detail_search(client, course):
    assert client.get(PUBLIC).data["count"] == 0
    course.status = "published"
    course.save()
    assert client.get(PUBLIC + course.slug + "/").status_code == 200
    assert client.get(PUBLIC, {"search": course.title}).data["count"] == 1
    assert client.get(PUBLIC, {"search": "no match"}).data["count"] == 0


def test_category_lookup(client, course):
    category = CategoryFactory()
    course.categories.add(category)
    course.status = "published"
    course.save()
    response = client.get(PUBLIC + f"category/{category.slug}/")
    assert response.status_code == 200
    assert [row["id"] for row in response.data] == [str(course.pk)]
    assert client.get(PUBLIC + "category/missing/").status_code == 404


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_management_requires_auth(client, course, method):
    target = MANAGE if method in ("get", "post") else MANAGE + f"{course.pk}/"
    assert getattr(client, method)(target).status_code == 401


def test_instructor_create_update_and_delete(client, instructor):
    client.force_authenticate(instructor)
    category = CategoryFactory()
    payload = {
        "title": "New",
        "short_description": "Short",
        "long_description": "Long",
        "learn_description_points": "Basics",
        "requirements": "None",
        "thumbnail": str(FileFactory().pk),
        "categories": [str(category.pk)],
    }
    response = client.post(MANAGE, payload, format="json")
    assert response.status_code == 201, response.data
    course = Course.objects.get(pk=response.data["id"])
    assert course.instructor == instructor
    target = MANAGE + f"{course.pk}/"
    assert client.patch(target, {"title": "Updated"}, format="json").status_code == 200
    course.refresh_from_db()
    assert course.title == "Updated"
    assert client.delete(target).status_code == 204
    course.refresh_from_db()
    assert course.is_deleted


def test_foreign_course_hidden_and_student_denied(client, instructor):
    foreign = CourseFactory()
    client.force_authenticate(instructor)
    assert client.patch(MANAGE + f"{foreign.pk}/", {}).status_code == 404
    client.force_authenticate(UserFactory())
    assert client.get(MANAGE).status_code == 403


def test_admin_can_restore(client, course):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="admin")[0])
    course.soft_delete()
    client.force_authenticate(user)
    assert client.delete(MANAGE + f"{course.pk}/").status_code == 200
    course.refresh_from_db()
    assert not course.is_deleted
