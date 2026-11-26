import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.common.models import Files
from apps.common.service import MAX_FILE_SIZE, FileService

pytestmark = pytest.mark.django_db


@pytest.fixture
def cloud(mocker):
    client = mocker.Mock()
    settings = mocker.patch("apps.common.service.settings")
    settings.AWS_STORAGE_BUCKET_NAME = "test-bucket"
    settings.AWS_REGION = "us-east-1"
    settings.CLOUDFRONT_DOMAIN = "https://cdn.example.com"
    mocker.patch("apps.common.service.boto3.client", return_value=client)
    return client.put_object


@pytest.mark.parametrize("content_type", ["image/png", "video/mp4", "application/pdf"])
def test_upload_persists_metadata(cloud, content_type):
    upload = SimpleUploadedFile("asset", b"content", content_type=content_type)
    result = FileService.upload_file_to_s3(upload, "category")
    cloud.assert_called_once()
    result.refresh_from_db()
    assert result.url.startswith("https://cdn.example.com/category/")
    assert result.name == "asset"
    assert result.type == content_type
    assert result.size == 7


@pytest.mark.parametrize(
    "content_type", ["text/plain", "application/zip", "application/octet-stream"]
)
def test_unsupported_type_does_not_upload(cloud, content_type):
    upload = SimpleUploadedFile("asset", b"data", content_type=content_type)
    with pytest.raises(ValueError, match="not allowed"):
        FileService.upload_file_to_s3(upload, "category")
    cloud.assert_not_called()
    assert not Files.objects.exists()


@pytest.mark.parametrize("extra", [0, 1])
def test_size_limit(cloud, extra):
    upload = SimpleUploadedFile(
        "image.png", b"x" * (MAX_FILE_SIZE + extra), content_type="image/png"
    )
    if extra:
        with pytest.raises(ValueError, match="too large"):
            FileService.upload_file_to_s3(upload, "category")
        cloud.assert_not_called()
        assert not Files.objects.exists()
    else:
        assert FileService.upload_file_to_s3(upload, "category").size == MAX_FILE_SIZE
        cloud.assert_called_once()


def test_cloud_failure_does_not_create_record(cloud):
    cloud.side_effect = RuntimeError("Cloud unavailable")
    upload = SimpleUploadedFile("image.png", b"data", content_type="image/png")
    with pytest.raises(ValueError, match="Cloud unavailable"):
        FileService.upload_file_to_s3(upload, "category")
    assert not Files.objects.exists()
