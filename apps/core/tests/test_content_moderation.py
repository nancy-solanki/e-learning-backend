import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.course.tests.factories import CourseFactory
from apps.lecture.tests.factories import LectureFactory
from apps.section.tests.factories import SectionFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(
    params=[
        ("course", CourseFactory),
        ("section", SectionFactory),
        ("lecture", LectureFactory),
    ]
)
def content(request):
    name, factory = request.param
    instance = factory()
    base = f"/api/v1/{name}/instructor/all/"
    return instance, base, f"{base}{instance.pk}/"


@pytest.fixture(params=["admin", "dual_role", "superuser"])
def admin_client(request):
    client = APIClient()
    user = UserFactory(is_superuser=request.param == "superuser")
    if request.param != "superuser":
        user.groups.add(Group.objects.get_or_create(name="admin")[0])
    if request.param == "dual_role":
        user.groups.add(Group.objects.get_or_create(name="instructor")[0])
    client.force_authenticate(user)
    return client


def test_admin_can_read_but_not_create(admin_client, content):
    instance, base, detail = content
    assert admin_client.get(base).status_code == 200
    assert admin_client.get(detail).status_code == 200
    assert admin_client.post(base, {}, format="json").status_code == 403


@pytest.mark.parametrize("method", ["patch", "put"])
def test_admin_can_only_update_status(admin_client, content, method):
    instance, _, detail = content
    send = getattr(admin_client, method)
    for value in instance.Status.values:
        response = send(detail, {"status": value}, format="json")
        assert response.status_code == 200, response.data
        instance.refresh_from_db()
        assert instance.status == value
    previous = instance.status
    assert send(detail, {"status": "invalid"}, format="json").status_code == 400
    instance.refresh_from_db()
    assert instance.status == previous


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "Changed"),
        ("reject_reason", "Reason"),
        ("deleted_at", None),
        ("instructor", "someone"),
        ("unknown", "value"),
    ],
)
@pytest.mark.parametrize("method", ["patch", "put"])
def test_admin_rejects_other_fields_atomically(
    admin_client, content, field, value, method
):
    instance, _, detail = content
    old_status, old_title = instance.status, instance.title
    response = getattr(admin_client, method)(
        detail, {"status": "published", field: value}, format="json"
    )
    assert response.status_code == 403
    instance.refresh_from_db()
    assert (instance.status, instance.title) == (old_status, old_title)


def test_admin_soft_delete_is_idempotent(admin_client, content):
    instance, _, detail = content
    expected = 200 if instance._meta.model_name == "lecture" else 204
    assert admin_client.delete(detail).status_code == expected
    instance.refresh_from_db()
    deleted_at = instance.deleted_at
    assert deleted_at is not None
    assert admin_client.delete(detail).status_code == expected
    instance.refresh_from_db()
    assert instance.deleted_at == deleted_at
    assert admin_client.get(detail).status_code == 200
