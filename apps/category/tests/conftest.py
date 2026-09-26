import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.category.tests.factories import CategoryFactory
from apps.common.tests.factories import FileFactory
from apps.users.tests.factories import SuperuserFactory


@pytest.fixture
def file_factory(db):
    return FileFactory


@pytest.fixture
def category_factory(db):
    return CategoryFactory


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
