from datetime import datetime, timezone
from decimal import Decimal

import pytest
from django.contrib.auth.models import Group

from apps.wallet.ledger import record_entry, settle_withdrawal
from apps.wallet.models import WalletEntry
from apps.wallet.tests.factories import WalletFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/wallet/"


@pytest.fixture(params=["admin", "instructor"])
def admin_wallet(client, request):
    wallet = WalletFactory(
        history_started_at=datetime(2026, 10, 1, tzinfo=timezone.utc)
    )
    wallet.user.groups.add(Group.objects.get_or_create(name=request.param)[0])
    client.force_authenticate(wallet.user)
    return wallet


def posting(wallet, amount, kind, reference, day=5, pending=False):
    entry = record_entry(
        wallet,
        amount=amount,
        kind=kind,
        reference=reference,
        description="Course",
        pending=pending,
    )
    date = datetime(2026, 10, day, tzinfo=timezone.utc)
    WalletEntry.objects.filter(pk=entry.pk).update(
        created_at=date, completed_at=None if pending else date
    )
    return entry


def test_overview_reconciles_and_filters_do_not_change_cards(client, admin_wallet):
    wallet = admin_wallet
    posting(wallet, 2800, "earning", "before", day=2)
    posting(wallet, 495, "earning", "sale")
    posting(wallet, -500, "withdrawal", "paid")
    posting(wallet, -89, "refund", "refund")
    posting(wallet, -250, "withdrawal", "pending", pending=True)
    response = client.get(
        BASE + "overview/",
        {"start": "2026-10-03", "end": "2026-10-10", "search": "nothing"},
    )
    assert response.status_code == 200
    data = response.data
    assert data["opening_balance"] == "2800.00"
    assert data["currency"] == "INR"
    assert data["payout_account"] is None
    assert data["summary"]["available_balance"] == "2456.00"
    assert data["summary"]["period_earnings"] == "495.00"
    assert data["summary"]["refunds"] == "89.00"
    assert data["summary"]["completed_payouts"] == "500.00"
    assert data["summary"]["pending_payout_count"] == 1
    assert data["summary"]["earning_count"] == 1


def test_reservation_settlement_and_idempotency(admin_wallet):
    wallet = admin_wallet
    posting(wallet, 100, "earning", "sale")
    entry = posting(wallet, -70, "withdrawal", "payout", pending=True)
    with pytest.raises(ValueError, match="Insufficient"):
        posting(wallet, -40, "withdrawal", "overdraft", pending=True)
    settle_withdrawal(entry, "completed")
    settle_withdrawal(entry, "completed")
    wallet.refresh_from_db()
    assert wallet.current_earnings == Decimal("30")
    assert wallet.total_withdraws == Decimal("70")
    assert posting(wallet, 100, "earning", "sale").reference == "sale"
    with pytest.raises(ValueError, match="different"):
        posting(wallet, 101, "earning", "sale")
    with pytest.raises(ValueError, match="already"):
        settle_withdrawal(entry, "failed")


def test_failed_reservation_releases_funds(client, admin_wallet):
    posting(admin_wallet, 100, "earning", "sale")
    entry = posting(admin_wallet, -100, "withdrawal", "payout", pending=True)
    settle_withdrawal(entry, "failed")
    assert (
        client.get(BASE + "overview/").data["summary"]["available_balance"] == "100.00"
    )


def test_history_filter_export_and_owner_isolation(client, admin_wallet):
    own = posting(admin_wallet, 12, "earning", "sale")
    foreign = posting(WalletFactory(), 15, "earning", "foreign")
    params = {"start": "2026-10-03", "end": "2026-10-10", "type": "earning"}
    response = client.get(BASE + "transactions/", params)
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(own.pk)
    assert client.get(BASE + f"transactions/{foreign.pk}/").status_code == 404
    assert client.get(BASE + f"transactions/{own.pk}/").status_code == 200
    WalletEntry.objects.filter(pk=own.pk).update(description="=EVIL()")
    export = client.get(BASE + "transactions/export/", params)
    assert export.status_code == 200
    assert "'=EVIL()" in export.content.decode()
    assert "foreign" not in export.content.decode()
    params["status"] = "pending"
    assert client.get(BASE + "transactions/", params).data["count"] == 0


@pytest.mark.parametrize(
    "path", ["", "overview/", "transactions/", "transactions/export/"]
)
def test_students_denied(client, path):
    wallet = WalletFactory()
    client.force_authenticate(wallet.user)
    assert client.get(BASE + path).status_code == 403


def test_dates_and_incomplete_history(client, admin_wallet):
    assert client.get(BASE + "overview/", {"start": "bad"}).status_code == 400
    assert (
        client.get(
            BASE + "overview/", {"start": "2026-10-10", "end": "2026-10-01"}
        ).status_code
        == 400
    )
    response = client.get(
        BASE + "overview/", {"start": "2026-09-01", "end": "2026-10-10"}
    )
    assert response.data["history_complete"] is False
    assert response.data["opening_balance"] is None


def test_migration_preserves_existing_balance(admin_wallet):
    from importlib import import_module
    from types import SimpleNamespace

    from django.apps import apps
    from django.db import connection

    admin_wallet.current_earnings = Decimal("123.45")
    admin_wallet.save()
    migrate = import_module(
        "apps.wallet.migrations.0002_wallet_currency_wallet_history_started_at_and_more"
    )
    migrate.opening_entries(apps, SimpleNamespace(connection=connection))
    entry = admin_wallet.entries.get()
    assert entry.type == "adjustment"
    assert entry.amount == Decimal("123.45")
    admin_wallet.refresh_from_db()
    assert admin_wallet.current_earnings == entry.amount
    assert admin_wallet.history_started_at == entry.completed_at


def test_superuser_and_anonymous(client):
    assert client.get(BASE + "overview/").status_code == 401
    wallet = WalletFactory()
    wallet.user.is_superuser = True
    wallet.user.save()
    client.force_authenticate(wallet.user)
    assert client.get(BASE + "overview/").status_code == 200
