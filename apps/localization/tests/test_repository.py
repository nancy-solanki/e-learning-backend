import pytest

from apps.localization.repository import LocalizationRepository

pytestmark = pytest.mark.django_db


def test_repository_lifecycle():
    obj = LocalizationRepository.create_localization(
        language_name="English", country="India"
    )
    assert list(LocalizationRepository.get_all_localizations()) == [obj]
    assert list(LocalizationRepository.get_active_localizations()) == [obj]
    LocalizationRepository.update_localization(obj, country="UK")
    obj.refresh_from_db()
    assert obj.country == "UK"
    LocalizationRepository.soft_delete_localization(obj)
    assert not LocalizationRepository.get_active_localizations().exists()
    assert obj in LocalizationRepository.get_all_localizations()
    LocalizationRepository.restore_localization(obj)
    obj.refresh_from_db()
    assert not obj.is_deleted
