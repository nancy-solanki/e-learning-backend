import pytest

pytestmark = pytest.mark.django_db


def test_soft_delete_and_restore(wallet):
    wallet.soft_delete()
    wallet.refresh_from_db()
    assert wallet.is_deleted
    wallet.restore()
    wallet.refresh_from_db()
    assert not wallet.is_deleted


def test_string(wallet):
    assert str(wallet) == str(wallet.user)


def test_toggle(wallet):
    assert wallet.toggle_deleted() == "deleted"
    wallet.refresh_from_db()
    assert wallet.is_deleted
    assert wallet.toggle_deleted() == "activated"
    wallet.refresh_from_db()
    assert not wallet.is_deleted
