import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.common.models import Files
from apps.common.service import MAX_FILE_SIZE, FileService

pytestmark = pytest.mark.django_db


@pytest.fixture
def cloud(mocker):
    return mocker.patch(
        "apps.common.service.cloudinary.uploader.upload",
        return_value={"secure_url": "https://example.com/upload.png"},
    )


@pytest.mark.parametrize("content_type", ["image/png", "video/mp4", "application/pdf"])
def test_upload_persists_metadata(cloud, content_type):
    upload = SimpleUploadedFile("asset", b"content", content_type=content_type)
    result = FileService.upload_file_to_cloud(upload, "category")
    cloud.assert_called_once_with(file=upload, folder="category")
    result.refresh_from_db()
    assert result.url == "https://example.com/upload.png"
    assert result.name == "asset"
    assert result.type == content_type
    assert result.size == 7


@pytest.mark.parametrize(
    "content_type", ["text/plain", "application/zip", "application/octet-stream"]
)
def test_unsupported_type_does_not_upload(cloud, content_type):
    upload = SimpleUploadedFile("asset", b"data", content_type=content_type)
    with pytest.raises(ValueError, match="not allowed"):
        FileService.upload_file_to_cloud(upload, "category")
    cloud.assert_not_called()
    assert not Files.objects.exists()


@pytest.mark.parametrize("extra", [0, 1])
def test_size_limit(cloud, extra):
    upload = SimpleUploadedFile(
        "image.png", b"x" * (MAX_FILE_SIZE + extra), content_type="image/png"
    )
    if extra:
        with pytest.raises(ValueError, match="too large"):
            FileService.upload_file_to_cloud(upload, "category")
        cloud.assert_not_called()
        assert not Files.objects.exists()
    else:
        assert (
            FileService.upload_file_to_cloud(upload, "category").size == MAX_FILE_SIZE
        )
        cloud.assert_called_once()


def test_cloud_failure_does_not_create_record(cloud):
    cloud.side_effect = RuntimeError("Cloud unavailable")
    upload = SimpleUploadedFile("image.png", b"data", content_type="image/png")
    with pytest.raises(ValueError, match="Cloud unavailable"):
        FileService.upload_file_to_cloud(upload, "category")
    assert not Files.objects.exists()
