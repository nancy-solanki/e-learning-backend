from datetime import timedelta
from uuid import UUID

import pytest
from django.utils import timezone

from apps.common.models import Files

pytestmark = pytest.mark.django_db


def test_base_model_identifiers_and_timestamps():
    before = timezone.now()
    first = Files.objects.create(url="https://example.com/first.png")
    second = Files.objects.create(url="https://example.com/second.png")
    first.refresh_from_db()
    assert isinstance(first.pk, UUID)
    assert first.pk != second.pk
    assert before <= first.created_at <= first.updated_at <= timezone.now()
    assert not first.is_deleted


def test_updates_preserve_creation_time(mocker):
    file = Files.objects.create(url="https://example.com/image.png")
    created = file.created_at
    later = file.updated_at + timedelta(minutes=1)
    mocker.patch("django.utils.timezone.now", return_value=later)
    file.name = "renamed"
    file.save()
    file.refresh_from_db()
    assert file.created_at == created
    assert file.updated_at == later


def test_explicit_created_at_is_preserved():
    created = timezone.now() - timedelta(days=5)
    file = Files.objects.create(url="https://example.com/image.png", created_at=created)
    file.refresh_from_db()
    assert file.created_at == created


def test_soft_delete_property_tracks_persisted_state():
    file = Files.objects.create(url="https://example.com/image.png")
    file.deleted_at = timezone.now()
    file.save()
    file.refresh_from_db()
    assert file.is_deleted
    file.deleted_at = None
    file.save()
    file.refresh_from_db()
    assert not file.is_deleted
