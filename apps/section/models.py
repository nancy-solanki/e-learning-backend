from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
import uuid

from apps.core.models import BaseModel


class Section(BaseModel):
    class Status(models.TextChoices):
        PUBLISHED = 'published', _('Published')
        DRAFT = 'draft', _('Draft')
        REJECTED = 'rejected', _('Rejected')

    title = models.CharField(_('title'), max_length=250)
    slug = models.SlugField(_('slug'), max_length=255, null=True, blank=True, unique=True)
    description = models.TextField(_('description'))
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )
    order = models.IntegerField(_('order'), default=0)
    instructor = models.ForeignKey(
        "users.User",
        on_delete=models.RESTRICT,
        verbose_name=_('instructor')
    )
    course = models.ForeignKey(
        "course.Course",
        on_delete=models.RESTRICT,
        related_name="sections",
        verbose_name=_('course')
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            self.slug = f"{self.slug}-{uuid.uuid4()}"
        return super().save(*args, **kwargs)

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
        return self.title

    class Meta:
        db_table = 'section'
        verbose_name = _('section')
        verbose_name_plural = _('sections')
        ordering = ["order", "-created_at"]
