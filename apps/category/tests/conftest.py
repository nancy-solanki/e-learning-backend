import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.category.models import Category
from apps.common.models import Files
from apps.users.tests.factories import SuperuserFactory, UserFactory


@pytest.fixture
def file_factory(db):
    def create():
        return Files.objects.create(
            url="https://example.com/image.png", name="image.png"
        )

    return create


@pytest.fixture
def category_factory(db, file_factory):
    def create(**kwargs):
        defaults = {
            "title": f"category {Category.objects.count()}",
            "description": "Learning resources",
            "user": UserFactory(),
            "thumbnail": file_factory(),
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)

    return create


@pytest.fixture
def category(category_factory):
    return category_factory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(api_client, db):
    api_client.force_authenticate(SuperuserFactory())
    return api_client


@pytest.fixture
def upload():
    return SimpleUploadedFile("image.png", b"image content", content_type="image/png")


@pytest.fixture
def cloud_upload(mocker, file_factory):
    # Keep file persistence real; only the external upload boundary is replaced.
    return mocker.patch(
        "apps.category.service.FileService.upload_file_to_cloud",
        side_effect=lambda *args: file_factory(),
    )
