import pytest

from apps.localization.tests.factories import LocalizationFactory

pytestmark = pytest.mark.django_db


def test_whitespace_normalized():
    obj = LocalizationFactory(language_name=" English ", country=" India ")
    obj.refresh_from_db()
    assert obj.language_name == "English"
    assert obj.country == "India"
    assert str(obj) == "English"


def test_idempotent_delete_restore_and_toggle(localization):
    localization.soft_delete()
    deleted_at = localization.deleted_at
    localization.soft_delete()
    localization.refresh_from_db()
    assert localization.deleted_at == deleted_at
    localization.restore()
    localization.restore()
    localization.refresh_from_db()
    assert not localization.is_deleted
    localization.toggle_deleted()
    assert localization.is_deleted
    localization.toggle_deleted()
    assert not localization.is_deleted
