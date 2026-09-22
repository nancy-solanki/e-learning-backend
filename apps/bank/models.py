from django.utils import timezone
from django.db import models
from apps.core.models import BaseModel

# Create your models here.
class Bank(BaseModel):
    name = models.CharField(max_length=200)
    ifsc_code = models.CharField(max_length=200)
    account_number = models.CharField(max_length=200, unique=True)
    default = models.BooleanField(default=False)
    user = models.ForeignKey(
        "users.User", on_delete=models.RESTRICT)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            has_bank = Bank.objects.filter(user=self.user).exists()
            if not has_bank:
                self.default = True
        super().save(*args, **kwargs)
    
    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
        return self

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
        return self

    def toggle_deleted(self):
        if self.is_deleted:
            return self.restore()
        return self.soft_delete()
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'bank'
        verbose_name = 'bank'
        verbose_name_plural = 'banks'