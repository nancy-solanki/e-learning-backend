import pytest
from django.urls import reverse

from apps.localization.models import Localization
from apps.users.tests.factories import SuperuserFactory, UserFactory

pytestmark = pytest.mark.django_db


def url(obj=None):
    if obj:
        return reverse("localization:localization-detail", kwargs={"pk": obj.pk})
    return reverse("localization:localization-list")


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
def test_anonymous_denied(client, localization, method):
    target = url() if method in ("get", "post") else url(localization)
    assert getattr(client, method)(target).status_code == 401


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_student_write_denied(client, localization, method):
    client.force_authenticate(UserFactory())
    target = url() if method == "post" else url(localization)
    assert getattr(client, method)(target).status_code == 403


def test_student_reads_only_active(client, localization):
    client.force_authenticate(UserFactory())
    assert client.get(url()).data["count"] == 1
    assert client.get(url(localization)).status_code == 200
    localization.soft_delete()
    assert client.get(url()).data["count"] == 0
    assert client.get(url(localization)).status_code == 404


def test_admin_crud_and_restore(client):
    client.force_authenticate(SuperuserFactory())
    response = client.post(
        url(), {"language_name": "English", "country": "India"}, format="json"
    )
    assert response.status_code == 201, response.data
    obj = Localization.objects.get(pk=response.data["id"])
    assert client.patch(url(obj), {"country": "UK"}, format="json").status_code == 200
    obj.refresh_from_db()
    assert obj.country == "UK"
    assert client.delete(url(obj)).status_code == 204
    obj.refresh_from_db()
    assert obj.is_deleted
    assert client.delete(url(obj)).status_code == 200
    obj.refresh_from_db()
    assert not obj.is_deleted


def test_invalid_create(client):
    client.force_authenticate(SuperuserFactory())
    assert client.post(url(), {"language_name": ""}, format="json").status_code == 400
    assert not Localization.objects.exists()
