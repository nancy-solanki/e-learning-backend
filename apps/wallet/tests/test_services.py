import pytest

from apps.wallet.service import WalletService
from apps.wallet.tests.factories import WalletFactory

pytestmark = pytest.mark.django_db


def test_queries_and_lifecycle(wallet):
    assert WalletService.get_wallet_by_user(wallet.user) == wallet
    assert list(WalletService.get_wallet_queryset_by_user(wallet.user)) == [wallet]
    site = WalletFactory(user=None, is_site_wallet=True)
    assert WalletService.get_site_wallet() == site
    WalletService.delete_wallet(wallet)
    assert WalletService.get_wallet_by_user(wallet.user) is None
    WalletService.restore_wallet(wallet)
    assert WalletService.get_wallet_by_user(wallet.user) == wallet
    assert WalletService.toggle_wallet_status(wallet) == "deleted"
