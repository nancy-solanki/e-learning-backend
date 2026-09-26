import pytest
from django.utils import timezone

from apps.wallet.repository import WalletRepository
from apps.wallet.tests.factories import WalletFactory

pytestmark = pytest.mark.django_db


def test_scope_and_site_wallet(wallet):
    WalletFactory(user=wallet.user, deleted_at=timezone.now())
    WalletFactory()
    assert list(WalletRepository.get_wallet_queryset_by_user(wallet.user)) == [wallet]
    assert WalletRepository.get_wallet_by_user(wallet.user) == wallet
    assert WalletRepository.get_site_wallet() is None
    site = WalletFactory(user=None, is_site_wallet=True)
    WalletFactory(user=None, is_site_wallet=True, deleted_at=timezone.now())
    assert WalletRepository.get_site_wallet() == site


def test_create_update(wallet):
    created = WalletRepository.create_wallet(user=wallet.user)
    assert WalletRepository.update_wallet(created, current_earnings=100) == created
    created.refresh_from_db()
    assert created.current_earnings == 100
