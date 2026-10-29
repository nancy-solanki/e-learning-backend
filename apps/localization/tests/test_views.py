import pytest
from django.contrib.auth.models import Group
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


@pytest.mark.parametrize("role", ["student", "instructor", "staff"])
@pytest.mark.parametrize("deleted", [False, True])
@pytest.mark.parametrize(
    "method,detail",
    [
        ("get", False),
        ("get", True),
        ("post", False),
        ("put", True),
        ("patch", True),
        ("delete", True),
        ("head", False),
        ("options", False),
    ],
)
def test_non_admin_denied(client, localization, role, deleted, method, detail):
    user = UserFactory(is_staff=role == "staff")
    user.groups.add(Group.objects.get_or_create(name=role)[0])
    client.force_authenticate(user)
    if deleted:
        localization.soft_delete()
    target = url(localization) if detail else url()
    assert getattr(client, method)(target).status_code == 403


@pytest.mark.parametrize("role", ["superuser", "admin"])
def test_admin_crud_and_restore(client, role):
    user = SuperuserFactory() if role == "superuser" else UserFactory()
    if role == "admin":
        user.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(user)
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
    assert client.get(url()).data["count"] == 1
    assert client.get(url(obj)).status_code == 200
    assert client.delete(url(obj)).status_code == 200
    obj.refresh_from_db()
    assert not obj.is_deleted


def test_invalid_create(client):
    client.force_authenticate(SuperuserFactory())
    assert client.post(url(), {"language_name": ""}, format="json").status_code == 400
    assert not Localization.objects.exists()


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"language_name": "english"}, ["English"]),
        ({"country": "india"}, ["English", "Hindi"]),
        ({"search": "hIN"}, ["Hindi"]),
        ({"search": "English India"}, ["English"]),
        ({"country": "India", "search": "English"}, ["English"]),
        ({"ordering": "-language_name"}, ["Hindi", "French", "English"]),
    ],
)
def test_list_filters_search_ordering(client, params, expected):
    from apps.localization.tests.factories import LocalizationFactory

    client.force_authenticate(SuperuserFactory())
    for language, country in [
        ("English", "India"),
        ("Hindi", "India"),
        ("French", "France"),
    ]:
        LocalizationFactory(language_name=language, country=country)
    response = client.get(url(), {"ordering": "language_name", **params})
    assert response.status_code == 200
    assert [obj["language_name"] for obj in response.data["results"]] == expected


def test_deleted_filter_respects_visibility(client):
    from apps.localization.tests.factories import LocalizationFactory

    client.force_authenticate(SuperuserFactory())
    active = LocalizationFactory()
    deleted = LocalizationFactory()
    deleted.soft_delete()
    response = client.get(url(), {"is_deleted": "true"})
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(deleted.pk)
    response = client.get(url(), {"is_deleted": "false"})
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(active.pk)


def test_pagination(client):
    from apps.localization.tests.factories import LocalizationFactory

    client.force_authenticate(SuperuserFactory())
    LocalizationFactory.create_batch(3)
    first = client.get(url(), {"page_size": 2}).data
    second = client.get(url(), {"page_size": 2, "page": 2}).data
    assert first["count"] == second["count"] == 3
    assert len(first["results"]) == 2
    assert first["next"] and first["previous"] is None
    assert len(second["results"]) == 1
    assert second["previous"] and second["next"] is None
    assert {obj["id"] for obj in first["results"]}.isdisjoint(
        obj["id"] for obj in second["results"]
    )
    assert client.get(url(), {"page": 3, "page_size": 2}).status_code == 404


@pytest.mark.parametrize(
    "size,expected", [(None, 20), ("bad", 20), (0, 20), (101, 100)]
)
def test_page_size_limits(client, size, expected):
    from apps.localization.tests.factories import LocalizationFactory

    client.force_authenticate(SuperuserFactory())
    LocalizationFactory.create_batch(101)
    response = client.get(url(), {} if size is None else {"page_size": size})
    assert response.data["count"] == 101
    assert len(response.data["results"]) == expected


@pytest.mark.parametrize("method", ["post", "put", "patch"])
def test_generated_fields_cannot_be_written(client, localization, method):
    client.force_authenticate(SuperuserFactory())
    payload = {
        "language_name": "English",
        "country": "India",
        "id": "00000000-0000-0000-0000-000000000001",
        "created_at": "2000-01-01T00:00:00Z",
        "updated_at": "2000-01-01T00:00:00Z",
        "deleted_at": "2000-01-01T00:00:00Z",
    }
    target = url() if method == "post" else url(localization)
    response = getattr(client, method)(target, payload, format="json")
    assert response.status_code == (201 if method == "post" else 200)
    assert response.data["id"] != payload["id"]
    assert response.data["created_at"] != payload["created_at"]
    assert response.data["updated_at"] != payload["updated_at"]
    assert response.data["deleted_at"] is None
    obj = Localization.objects.get(pk=response.data["id"])
    assert not obj.is_deleted
    if method != "post":
        assert obj.pk == localization.pk
        assert obj.created_at == localization.created_at


@pytest.mark.parametrize("authentication", ["bearer", "cookie"])
def test_instructor_list_denied_with_jwt(
    client, instructor, localization, authentication
):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(instructor).access_token)
    if authentication == "bearer":
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    else:
        client.cookies["access_token"] = token
    assert client.get(url()).status_code == 403
