from django.db import models
from django.utils import timezone

from apps.core.models import BaseModel


class Localization(BaseModel):
    language_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        self.language_name = self.language_name.strip()
        self.country = self.country.strip()
        super().save(*args, **kwargs)

    def soft_delete(self):
        if not self.deleted_at:
            self.deleted_at = timezone.now()
            self.save(update_fields=["deleted_at"])
        return self

    def restore(self):
        if self.deleted_at:
            self.deleted_at = None
            self.save(update_fields=["deleted_at"])
        return self

    def toggle_deleted(self):
        return self.restore() if self.is_deleted else self.soft_delete()

    def __str__(self):
        return self.language_name
