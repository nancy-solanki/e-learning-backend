import pytest

from apps.enroll.tests.factories import EnrollFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/enroll/management/"


def test_auth_and_user_scoping(client, enroll):
    assert client.get(BASE).status_code == 401
    EnrollFactory()
    client.force_authenticate(enroll.user)
    response = client.get(BASE)
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(enroll.pk)
    assert client.get(BASE + f"{enroll.pk}/").status_code == 200
    client.force_authenticate(UserFactory())
    assert client.get(BASE + f"{enroll.pk}/").status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_read_only(client, enroll, method):
    client.force_authenticate(enroll.user)
    target = BASE if method == "post" else BASE + f"{enroll.pk}/"
    assert getattr(client, method)(target).status_code == 405


def test_instructor_and_search(client, enroll):
    enroll.course.instructor.become_instructor()
    client.force_authenticate(enroll.course.instructor)
    assert client.get(BASE, {"search": enroll.course.title}).data["count"] == 1
    assert client.get(BASE, {"search": "missing"}).data["count"] == 0


def test_course_lookup(client, enroll):
    client.force_authenticate(enroll.course.instructor)
    target = f"/api/v1/enroll/course/{enroll.course.slug}/"
    assert client.get(target).status_code == 404
    enroll.course.status = "published"
    enroll.course.save()
    response = client.get(target)
    assert response.status_code == 200
    assert response.data[0]["id"] == str(enroll.pk)
    enroll.soft_delete()
    assert client.get(target).status_code == 404
