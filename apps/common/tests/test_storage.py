from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.db import models

from apps.lecture.models import Lecture


def test_lecture_thumbnail_uploads_to_cloudinary(settings, mocker):
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
    storage = Lecture._meta.get_field("thumbnail").storage
    name = storage.save("lecture/test.png", ContentFile(b"test content"))

    upload.assert_called_once()
    assert upload.call_args.kwargs["resource_type"] == "image"
    assert upload.call_args.kwargs["folder"] == "media/lecture"
    assert name == "media/lecture/test-asset"
    assert storage.url(name).startswith(
        "https://res.cloudinary.com/test-cloud/image/upload/"
    )


def test_lecture_video_source_is_an_s3_key_field():
    assert isinstance(Lecture._meta.get_field("source"), models.CharField)


def test_static_assets_keep_local_storage():
    from django.contrib.staticfiles.storage import StaticFilesStorage

    assert isinstance(storages["staticfiles"], StaticFilesStorage)
