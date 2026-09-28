import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import storages

from apps.lecture.models import Lecture


@pytest.mark.parametrize(
    "field, resource_type, extension",
    [("thumbnail", "image", "png"), ("source", "video", "mp4")],
)
def test_lecture_media_uploads_to_cloudinary(
    settings, mocker, field, resource_type, extension
):
    settings.CLOUDINARY_STORAGE = {
        "CLOUD_NAME": "test-cloud",
        "API_KEY": "test-key",
        "API_SECRET": "test-secret",
        "SECURE": True,
    }
    upload = mocker.patch(
        "cloudinary.uploader.upload",
        return_value={"public_id": "media/lecture/test-asset"},
    )
    storage = Lecture._meta.get_field(field).storage
    name = storage.save(f"lecture/test.{extension}", ContentFile(b"test content"))

    upload.assert_called_once()
    assert upload.call_args.kwargs["resource_type"] == resource_type
    assert upload.call_args.kwargs["folder"] == "media/lecture"
    assert name == "media/lecture/test-asset"
    assert storage.url(name).startswith(
        f"https://res.cloudinary.com/test-cloud/{resource_type}/upload/"
    )


def test_static_assets_keep_local_storage():
    from django.contrib.staticfiles.storage import StaticFilesStorage

    assert isinstance(storages["staticfiles"], StaticFilesStorage)
