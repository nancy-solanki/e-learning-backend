from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.core.models import BaseModel

# Create your models here.


class Wallet(BaseModel):
    current_earnings = models.IntegerField(default=0)
    total_earnings = models.IntegerField(default=0)
    total_withdraws = models.IntegerField(default=0)
    is_site_wallet = models.BooleanField(default=False)
    user = models.ForeignKey(
        "users.User", on_delete=models.RESTRICT, null=True)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
        return self

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
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
        db_table = 'wallet'
        verbose_name = _('wallet')
        verbose_name_plural = _('wallets')