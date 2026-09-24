from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.utils.text import slugify
from django.db import models
import random

from apps.core.models import BaseModel


class Tag(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tag'
        verbose_name = 'tag'
        verbose_name_plural = 'tags'
        ordering = ["name"]


class Course(BaseModel):
    class Status(models.TextChoices):
        PUBLISHED = ('published', 'Published')
        IN_REVIEW = ('in-review', 'In Review')
        APPROVED = ('approved', 'Approved')
        DRAFT = ('draft', 'Draft')
        REJECTED = ('rejected', 'Rejected')

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    short_description = models.TextField()
    long_description = models.TextField()
    is_free = models.BooleanField(default=False)
    price = models.IntegerField(default=0)
    status = models.CharField(max_length=9, choices=Status.choices, default=Status.DRAFT)
    reject_reason = models.TextField(null=True, blank=True)
    is_best_seller = models.BooleanField(default=False)
    learn_description_points = models.TextField()
    requirements = models.TextField()
    total_hours = models.CharField(default="00:00:00", max_length=20)
    total_articles = models.IntegerField(default=0)
    thumbnail = models.OneToOneField('common.Files', related_name='course', on_delete=models.CASCADE)
    # keywords = ArrayField(models.CharField(max_length=200), db_index=True)  # Replaced with tags
    instructor = models.ForeignKey(
        "users.User", on_delete=models.RESTRICT)
    categories = models.ManyToManyField(
        "category.Category", related_name="category")
    tags = models.ManyToManyField(Tag, related_name="courses", blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            self.slug = self.slug + '-' + str(random.randint(500, 9000))
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
        return self.title

    class Meta:
        db_table = 'course'
        verbose_name = 'course'
        verbose_name_plural = 'courses'
