from django.core.files.storage import storages
from django.db import models

from apps.lecture.models import Lecture


def test_lecture_thumbnail_uses_s3_storage():
    storage = Lecture._meta.get_field("thumbnail").storage
    assert storage.__class__.__module__.startswith("storages.backends.s3")


def test_lecture_video_source_is_an_s3_key_field():
    assert isinstance(Lecture._meta.get_field("source"), models.CharField)


def test_static_assets_keep_local_storage():
    from django.contrib.staticfiles.storage import StaticFilesStorage

    assert isinstance(storages["staticfiles"], StaticFilesStorage)
