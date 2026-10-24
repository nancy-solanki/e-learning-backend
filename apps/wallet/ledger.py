from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Wallet, WalletEntry


@transaction.atomic
def record_entry(
    wallet, *, reference, amount, kind, description, pending=False, account_last4=""
):
    """Internal posting API. References are idempotency keys; amounts are signed INR."""
    wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
    amount = Decimal(str(amount))
    if not amount.is_finite() or amount != amount.quantize(Decimal("0.01")):
        raise ValueError("Amount must have at most two decimal places")
    if kind not in WalletEntry.Kind.values or kind == "adjustment":
        raise ValueError("Unsupported posting kind")
    if (kind == "earning" and amount <= 0) or (kind != "earning" and amount >= 0):
        raise ValueError("Invalid amount direction")
    if pending and kind != "withdrawal":
        raise ValueError("Only withdrawals can be pending")
    existing = WalletEntry.objects.filter(reference=reference).first()
    if existing:
        if (
            existing.wallet_id != wallet.pk
            or existing.amount != amount
            or existing.type != kind
        ):
            raise ValueError("Reference already used for a different posting")
        return existing
    reserved = sum(
        (-e.amount for e in wallet.entries.filter(status="pending", type="withdrawal")),
        Decimal(0),
    )
    if kind == "withdrawal" and wallet.current_earnings - reserved + amount < 0:
        raise ValueError("Insufficient available balance")
    now = timezone.now()
    entry = WalletEntry.objects.create(
        wallet=wallet,
        reference=reference,
        amount=amount,
        type=kind,
        description=description,
        status="pending" if pending else "completed",
        completed_at=None if pending else now,
        account_last4=account_last4,
    )
    if not pending:
        wallet.current_earnings += amount
        if kind == "earning":
            wallet.total_earnings += amount
        elif kind == "withdrawal":
            wallet.total_withdraws -= amount
        wallet.save(
            update_fields=["current_earnings", "total_earnings", "total_withdraws"]
        )
    return entry


@transaction.atomic
def settle_withdrawal(entry, status):
    wallet = Wallet.objects.select_for_update().get(pk=entry.wallet_id)
    entry = WalletEntry.objects.select_for_update().get(pk=entry.pk)
    if entry.type != "withdrawal" or status not in ("completed", "failed", "cancelled"):
        raise ValueError("Invalid withdrawal transition")
    if entry.status == status:
        return entry
    if entry.status != "pending":
        raise ValueError("Withdrawal has already been settled")
    entry.status = status
    if status == "completed":
        entry.completed_at = timezone.now()
        wallet.current_earnings += entry.amount
        wallet.total_withdraws -= entry.amount
        wallet.save(update_fields=["current_earnings", "total_withdraws"])
    entry.save(update_fields=["status", "completed_at"])
    return entry
