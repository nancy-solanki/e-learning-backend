import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

# Create your models here.


class Wallet(BaseModel):
    current_earnings = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_withdraws = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="INR")
    history_started_at = models.DateTimeField(default=timezone.now)
    is_site_wallet = models.BooleanField(default=False)
    user = models.ForeignKey("users.User", on_delete=models.RESTRICT, null=True)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return self

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
        return self

    def toggle_deleted(self) -> str:
        if self.is_deleted:
            self.restore()
            return "activated"
        self.soft_delete()
        return "deleted"

    def __str__(self):
        return str(self.user)

    class Meta:
        db_table = "wallet"
        verbose_name = _("wallet")
        verbose_name_plural = _("wallets")


class WalletEntry(models.Model):
    """Wallet-specific ledger, separate from customer payment transactions."""

    class Kind(models.TextChoices):
        EARNING = "earning", "Earning"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        REFUND = "refund", "Refund"
        ADJUSTMENT = "adjustment", "Adjustment"

    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        PENDING = "pending", "Pending"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="entries")
    reference = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    type = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(max_length=16, choices=Status.choices)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    account_last4 = models.CharField(max_length=4, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
