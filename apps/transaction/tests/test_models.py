import pytest

pytestmark = pytest.mark.django_db


def test_soft_delete_and_restore(transaction):
    transaction.soft_delete()
    transaction.refresh_from_db()
    assert transaction.is_deleted
    transaction.restore()
    transaction.refresh_from_db()
    assert not transaction.is_deleted


def test_string(transaction):
    assert (
        str(transaction)
        == f"{transaction.transaction_type} - {transaction.amount} - {transaction.user}"
    )


def test_toggle(transaction):
    assert transaction.toggle_deleted() == "deleted"
    transaction.refresh_from_db()
    assert transaction.is_deleted
    assert transaction.toggle_deleted() == "activated"
    transaction.refresh_from_db()
    assert not transaction.is_deleted


def test_unique_transaction_id(transaction):
    from django.db import IntegrityError
    from django.db import transaction as db_transaction

    from apps.transaction.tests.factories import TransactionFactory

    with pytest.raises(IntegrityError), db_transaction.atomic():
        TransactionFactory(tx_id=transaction.tx_id)
