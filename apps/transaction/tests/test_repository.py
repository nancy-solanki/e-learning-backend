from uuid import uuid4

import pytest
from django.utils import timezone

from apps.transaction.repository import TransactionRepository
from apps.transaction.tests.factories import TransactionFactory

pytestmark = pytest.mark.django_db


def test_scoping(transaction):
    foreign = TransactionFactory()
    TransactionFactory(user=transaction.user, deleted_at=timezone.now())
    assert set(TransactionRepository.get_transaction_queryset()) == {
        transaction,
        foreign,
    }
    assert list(TransactionRepository.get_user_transactions(transaction.user)) == [
        transaction
    ]
    assert TransactionRepository.get_transaction_by_id(transaction.pk) == transaction
    assert TransactionRepository.get_transaction_by_id(uuid4()) is None


def test_lifecycle(transaction):
    TransactionRepository.soft_delete_transaction(transaction)
    assert TransactionRepository.get_transaction_by_id(transaction.pk) is None
    TransactionRepository.restore_transaction(transaction)
    assert TransactionRepository.get_transaction_by_id(transaction.pk) == transaction
    assert TransactionRepository.toggle_transaction_status(transaction) == "deleted"
