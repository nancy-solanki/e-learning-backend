from django.db import models

from apps.core.models import BaseModel

# Create your models here.


class Files(BaseModel):
    url = models.URLField(max_length=300)
    name = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "file"
        verbose_name = "file"
        verbose_name_plural = "files"
        ordering = ["-created_at"]
