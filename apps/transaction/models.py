from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Transaction(BaseModel):
    class STATUS(models.TextChoices):
        SUCCESS = ("success", "Success")
        REJECTED = ("rejected", "Rejected")
        PENDING = ("pending", "Pending")
        FAILED = ("failed", "Failed")

    class TYPE(models.TextChoices):
        CREDIT = ("credit", "Credit")
        DEBIT = ("debit", "Debit")

    user = models.ForeignKey(
        "users.User", on_delete=models.RESTRICT, related_name="transactions"
    )
    wallet = models.ForeignKey(
        "wallet.Wallet",
        on_delete=models.RESTRICT,
        related_name="transactions",
        null=True,
        blank=True,
    )
    amount = models.IntegerField(default=0)
    status = models.CharField(
        max_length=10, choices=STATUS.choices, default=STATUS.PENDING
    )
    transaction_type = models.CharField(max_length=10, choices=TYPE.choices)
    description = models.TextField(null=True, blank=True)
    tx_id = models.CharField(max_length=255, null=True, blank=True, unique=True)

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
        return f"{self.transaction_type} - {self.amount} - {self.user}"

    class Meta:
        db_table = "transaction"
        verbose_name = _("transaction")
        verbose_name_plural = _("transactions")
        ordering = ("-created_at",)
