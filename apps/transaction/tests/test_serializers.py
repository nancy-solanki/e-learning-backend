import pytest

from apps.transaction.serializers import TransactionSerializer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "field,value",
    [("status", "invalid"), ("transaction_type", "invalid"), ("amount", "bad")],
)
def test_invalid_fields(transaction, field, value):
    serializer = TransactionSerializer(transaction, data={field: value}, partial=True)
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_metadata_readonly(transaction):
    serializer = TransactionSerializer(
        transaction,
        data={
            "deleted_at": "2026-01-01T00:00:00Z",
            "created_at": "2020-01-01T00:00:00Z",
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data == {}


def test_duplicate_tx_id(transaction):
    serializer = TransactionSerializer(
        data={
            "user": str(transaction.user_id),
            "transaction_type": "credit",
            "tx_id": transaction.tx_id,
        }
    )
    assert not serializer.is_valid()
    assert "tx_id" in serializer.errors
