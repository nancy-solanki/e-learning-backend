import random
from django.db import models
from django.utils.text import slugify

from apps.core.models import BaseModel

# Create your models here.


class Category(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='categories')
    thumbnail = models.OneToOneField('common.Files', related_name='category', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.title = self.title.lower()
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'category'
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ["-created_at"]
