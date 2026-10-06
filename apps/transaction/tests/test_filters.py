from datetime import datetime, timezone

import pytest

from apps.transaction.tests.factories import TransactionFactory
from apps.wallet.tests.factories import WalletFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/transaction/"


@pytest.fixture
def transactions(client):
    wallet = WalletFactory()
    matched = TransactionFactory(
        user=wallet.user,
        wallet=wallet,
        amount=150,
        status="success",
        transaction_type="credit",
        tx_id="payment_unique_123",
        description="Python course payment",
        created_at=datetime(2026, 1, 15, 12, tzinfo=timezone.utc),
    )
    other = TransactionFactory(
        user=wallet.user,
        wallet=None,
        amount=50,
        status="failed",
        transaction_type="debit",
        description=None,
        tx_id=None,
        created_at=datetime(2026, 1, 17, 12, tzinfo=timezone.utc),
    )
    deleted = TransactionFactory(user=wallet.user, wallet=wallet, status="success")
    deleted.soft_delete()
    foreign = TransactionFactory(status="success")
    client.force_authenticate(wallet.user)
    return matched, other, deleted, foreign


@pytest.mark.parametrize(
    "query",
    [
        {"status": "success"},
        {"transaction_type": "credit"},
        {"tx_id": "payment_unique_123"},
        {"amount_min": "150", "amount_max": "150"},
        {"created_at_after": "2026-01-15", "created_at_before": "2026-01-15"},
        {"search": "UNIQUE_123"},
        {"search": "PYTHON payment"},
        {"search": "course", "status": "success", "amount_min": "100"},
    ],
)
def test_filters(client, transactions, query):
    matched, _, _, _ = transactions
    response = client.get(BASE, query)
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(matched.pk)]


def test_wallet_filter(client, transactions):
    matched, _, _, _ = transactions
    response = client.get(BASE, {"wallet": str(matched.wallet_id)})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(matched.pk)]


def test_search_id_preserves_scope(client, transactions):
    matched, _, deleted, foreign = transactions
    assert client.get(BASE, {"search": str(matched.pk)}).data["count"] == 1
    for hidden in [deleted, foreign]:
        response = client.get(BASE, {"search": str(hidden.pk)})
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert client.get(BASE, {"tx_id": hidden.tx_id}).data["count"] == 0


@pytest.mark.parametrize(
    "query",
    [
        {"search": "no-match-xyz"},
        {"amount_min": "151"},
        {"amount_max": "49"},
        {"created_at_after": "2026-01-18"},
        {"created_at_before": "2026-01-14"},
        {"tx_id": "unique_123"},
    ],
)
def test_empty_results(client, transactions, query):
    response = client.get(BASE, query)
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.parametrize(
    "field",
    [
        "status",
        "transaction_type",
        "wallet",
        "amount_min",
        "amount_max",
        "created_at_after",
        "created_at_before",
    ],
)
def test_invalid_filters(client, transactions, field):
    response = client.get(BASE, {field: "invalid"})
    assert response.status_code == 400
    assert field in response.data


@pytest.mark.parametrize("ordering", ["created_at", "-created_at", "amount", "-amount"])
def test_ordering(client, transactions, ordering):
    matched, other, _, _ = transactions
    expected = (
        [matched, other] if ordering in ("created_at", "-amount") else [other, matched]
    )
    response = client.get(BASE, {"ordering": ordering})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [
        str(row.pk) for row in expected
    ]


def test_nullable_fields_and_debit_filter(client, transactions):
    _, other, _, _ = transactions
    response = client.get(BASE, {"transaction_type": "debit", "status": "failed"})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(other.pk)]
