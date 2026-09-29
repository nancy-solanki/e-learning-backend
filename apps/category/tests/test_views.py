import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from apps.category.models import Category
from apps.category.service import CategoryService
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def list_url():
    return reverse("category:category-list")


def detail_url(category):
    return reverse("category:category-detail", kwargs={"slug": category.slug})


def test_public_list_and_retrieve(api_client, category):
    response = api_client.get(list_url())
    assert response.status_code == 200
    assert response.data["count"] == 1
    response = api_client.get(detail_url(category))
    assert response.status_code == 200
    assert response.data["thumbnail"]["url"] == category.thumbnail.url


@pytest.mark.parametrize("role, expected", [("anonymous", 401), ("user", 403)])
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_write_permissions(api_client, category, cloud_upload, role, expected, method):
    if role == "user":
        api_client.force_authenticate(UserFactory())
    url = list_url() if method == "post" else detail_url(category)
    response = getattr(api_client, method)(url, {}, format="multipart")
    assert response.status_code == expected
    cloud_upload.assert_not_called()
    category.refresh_from_db()
    assert category.deleted_at is None


@pytest.mark.parametrize("role", ["superuser", "admin_group"])
def test_create(admin_client, upload, cloud_upload, role):
    if role == "admin_group":
        user = UserFactory()
        user.groups.add(Group.objects.get_or_create(name="admin")[0])
        admin_client.force_authenticate(user)
    response = admin_client.post(
        list_url(),
        {"title": "Python", "description": "Learn", "thumbnail": upload},
        format="multipart",
    )
    assert response.status_code == 201, response.data
    category = Category.objects.get(slug="python")
    assert category.user == admin_client.handler._force_user
    assert response.data["thumbnail"]["url"] == category.thumbnail.url
    cloud_upload.assert_called_once()


@pytest.mark.parametrize("method", ["post", "put"])
def test_missing_thumbnail(admin_client, category, method):
    url = list_url() if method == "post" else detail_url(category)
    response = getattr(admin_client, method)(
        url, {"title": "New", "description": "Learn"}, format="multipart"
    )
    assert response.status_code == 400
    assert response.data["detail"] == "Thumbnail is required."


@pytest.mark.parametrize("method", ["post", "put", "patch"])
def test_invalid_data_does_not_upload(
    admin_client, category, upload, cloud_upload, method
):
    url = list_url() if method == "post" else detail_url(category)
    response = getattr(admin_client, method)(
        url, {"title": "", "thumbnail": upload}, format="multipart"
    )
    assert response.status_code == 400
    cloud_upload.assert_not_called()


@pytest.mark.parametrize("method", ["post", "put", "patch"])
def test_upload_failure(admin_client, category, upload, cloud_upload, method):
    cloud_upload.side_effect = ValueError("Upload failed")
    url = list_url() if method == "post" else detail_url(category)
    response = getattr(admin_client, method)(
        url,
        {"title": "New", "description": "Learn", "thumbnail": upload},
        format="multipart",
    )
    assert response.status_code == 400
    assert Category.objects.count() == 1
    category.refresh_from_db()
    assert category.title != "new"


@pytest.mark.parametrize("method", ["put", "patch"])
def test_update_thumbnail(admin_client, category, upload, cloud_upload, method):
    previous = category.thumbnail_id
    response = getattr(admin_client, method)(
        detail_url(category),
        {"title": "Updated", "description": "Updated", "thumbnail": upload},
        format="multipart",
    )
    assert response.status_code == 200, response.data
    category.refresh_from_db()
    assert category.title == "updated"
    assert category.thumbnail_id != previous


def test_description_only_patch(admin_client, category, cloud_upload):
    response = admin_client.patch(
        detail_url(category), {"description": "Updated"}, format="multipart"
    )
    assert response.status_code == 200, response.data
    category.refresh_from_db()
    assert category.description == "Updated"
    cloud_upload.assert_not_called()


def test_delete_hides_category(admin_client, api_client, category):
    url = detail_url(category)
    assert admin_client.delete(url).status_code == 204
    category.refresh_from_db()
    assert category.deleted_at is not None
    assert api_client.get(url).status_code == 404
    assert api_client.get(list_url()).data["count"] == 0
    assert admin_client.delete(url).status_code == 404


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_deleted_category_unavailable(admin_client, category, method):
    CategoryService.delete_category(category)
    response = getattr(admin_client, method)(detail_url(category))
    assert response.status_code == 404


@pytest.mark.parametrize(
    "query", [{"search": "python"}, {"title": "python"}, {"slug": "python"}]
)
def test_filtering(api_client, category_factory, query):
    category_factory(title="Python")
    category_factory(title="Java")
    response = api_client.get(list_url(), query)
    assert response.status_code == 200
    assert [row["title"] for row in response.data["results"]] == ["python"]


def test_ordering(api_client, category_factory):
    category_factory(title="Python")
    category_factory(title="Java")
    response = api_client.get(list_url(), {"ordering": "title"})
    assert [row["title"] for row in response.data["results"]] == ["java", "python"]


@pytest.mark.parametrize(
    "query",
    [
        {"title": "PYTHON"},
        {"slug": "PYTHON"},
        {"search": "CODING"},
        {"search": "python", "title": "PYTHON", "ordering": "title"},
    ],
)
def test_case_insensitive_filters_and_description_search(
    api_client, category_factory, query
):
    category_factory(title="Python", description="Coding lessons")
    category_factory(title="Java", description="Other lessons")
    response = api_client.get(list_url(), query)
    assert response.status_code == 200
    assert [row["title"] for row in response.data["results"]] == ["python"]


def test_category_pagination(api_client, category_factory):
    for i in range(21):
        category_factory(title=f"Category {i:02d}")
    default = api_client.get(list_url())
    assert default.data["count"] == 21
    assert len(default.data["results"]) == 20
    first = api_client.get(
        list_url(), {"search": "category", "page_size": 10, "ordering": "title"}
    )
    second = api_client.get(first.data["next"])
    third = api_client.get(second.data["next"])
    assert len(first.data["results"]) == len(second.data["results"]) == 10
    assert len(third.data["results"]) == 1
    assert first.data["previous"] is None
    assert third.data["next"] is None
    assert api_client.get(second.data["previous"]).data == first.data
    rows = first.data["results"] + second.data["results"] + third.data["results"]
    assert len({row["id"] for row in rows}) == 21
    assert api_client.get(list_url(), {"page": "invalid"}).status_code == 404
    assert api_client.get(list_url(), {"page": 99}).status_code == 404


def test_category_page_size_cap(api_client, category_factory):
    category_factory.create_batch(101)
    response = api_client.get(list_url(), {"page_size": 200})
    assert response.data["count"] == 101
    assert len(response.data["results"]) == 100
