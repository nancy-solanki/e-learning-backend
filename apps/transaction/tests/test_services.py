import pytest

from apps.transaction.service import TransactionService
from apps.users.tests.factories import UserFactory
from apps.wallet.tests.factories import WalletFactory

pytestmark = pytest.mark.django_db


def test_create_defaults_and_status():
    user = UserFactory()
    transaction = TransactionService.create_transaction(user, 100, "credit")
    assert transaction.status == "pending"
    assert transaction.wallet is None
    assert transaction.tx_id is None
    TransactionService.update_transaction_status(transaction, "success")
    transaction.refresh_from_db()
    assert transaction.status == "success"
    assert list(TransactionService.get_transaction_queryset()) == [transaction]
    assert list(TransactionService.get_user_transactions(user)) == [transaction]
    assert not TransactionService.get_user_transactions(UserFactory()).exists()


def test_optional_fields():
    wallet = WalletFactory()
    transaction = TransactionService.create_transaction(
        wallet.user,
        25,
        "debit",
        status="success",
        wallet=wallet,
        description="Withdrawal",
        tx_id="withdrawal-1",
    )
    transaction.refresh_from_db()
    assert transaction.wallet == wallet
    assert transaction.description == "Withdrawal"
    assert transaction.tx_id == "withdrawal-1"
    assert transaction.amount == 25
