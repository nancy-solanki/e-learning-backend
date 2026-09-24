import random

from cloudinary_storage.storage import (
    VideoMediaCloudinaryStorage,
)
from cloudinary_storage.validators import validate_video
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Lecture(BaseModel):
    class Status(models.TextChoices):
        PUBLISHED = ("published", "Published")
        DRAFT = ("draft", "Draft")
        REJECTED = ("rejected", "Rejected")

    class LectureType(models.TextChoices):
        VIDEO = ("video", "Video")
        DOCUMENT = ("document", "Document")

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    description = models.TextField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    lecture_type = models.CharField(
        max_length=10, choices=LectureType.choices, default=LectureType.VIDEO
    )
    source = models.FileField(
        upload_to="lecture/",
        storage=VideoMediaCloudinaryStorage(),
        validators=[validate_video],
        null=True,
        blank=True,
    )
    is_preview = models.BooleanField(default=False)
    document_content = models.TextField(null=True, blank=True)
    reject_reason = models.TextField(null=True)
    resources = models.JSONField(null=True, blank=True)
    order = models.IntegerField(default=0)
    thumbnail = models.ImageField(upload_to="lecture/", null=True)
    instructor = models.ForeignKey("users.User", on_delete=models.RESTRICT)
    course = models.ForeignKey(
        "course.Course", on_delete=models.RESTRICT, related_name="lecture"
    )
    section = models.ForeignKey(
        "section.Section", on_delete=models.RESTRICT, related_name="lecture"
    )
    duration = models.CharField(null=True, blank=True, max_length=10)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            self.slug = f"{self.slug}-{random.randint(500, 9000)}"
        return super().save(*args, **kwargs)

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return self

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
        return self

    def toggle_deleted(self) -> str:
        if self.deleted_at:
            self.restore()
            return "activated"
        self.soft_delete()
        return "deleted"

    def __str__(self) -> str:
        return self.title

    class Meta:
        db_table = "lecture"
        verbose_name = _("lecture")
        verbose_name_plural = _("lectures")
        ordering = ["order", "-created_at"]
