import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.


class CoreModel(models.Model):
    """
    Core Model providing a base class for Django's model.Model.
    """

    class Meta:
        abstract = True


class TimestampModel(CoreModel):
    """
    Timestamped Model supporting timestamp fields.

    Fields:
        - created_at
        - updated_at
    """

    created_at = models.DateTimeField(_("created at"), blank=True, null=True)
    updated_at = models.DateTimeField(_("updated at"), blank=True, null=True, auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        # If created_at and updated is not provided, set it to the current timestamp
        if not self.created_at and not self.updated_at:
            self.created_at = timezone.now()
            self.updated_at = timezone.now()

        super().save(*args, **kwargs)


class SoftDeleteModel(CoreModel):
    """
    Models for soft-delete functionality is supported.

    Fields:
        - deleted_at: DateTimeField, nullable and blank.
    """

    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at not in [None, ""]


class UUIDModel(CoreModel):
    """
    UUID Model supporting UUID fields.
    """

    id = models.UUIDField(_("primary key"), primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(TimestampModel, SoftDeleteModel, UUIDModel):
    """
    Base Model supporting timestamp and soft delete functionality.
    """

    class Meta:
        abstract = True
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Create your models here.


class CoreModel(models.Model):
    """
    Core Model providing a base class for Django's model.Model.
    """

    class Meta:
        abstract = True


class TimestampModel(CoreModel):
    """
    Timestamped Model supporting timestamp fields.

    Fields:
        - created_at
        - updated_at
    """

    created_at = models.DateTimeField(_("created at"), blank=True, null=True)
    updated_at = models.DateTimeField(_("updated at"), blank=True, null=True, auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        # If created_at and updated is not provided, set it to the current timestamp
        if not self.created_at and not self.updated_at:
            self.created_at = timezone.now()
            self.updated_at = timezone.now()

        super().save(*args, **kwargs)


class SoftDeleteModel(CoreModel):
    """
    Models for soft-delete functionality is supported.

    Fields:
        - deleted_at: DateTimeField, nullable and blank.
    """

    deleted_at = models.DateTimeField(_("deleted at"), null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at not in [None, ""]


class UUIDModel(CoreModel):
    """
    UUID Model supporting UUID fields.
    """

    id = models.UUIDField(_("primary key"), primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(TimestampModel, SoftDeleteModel, UUIDModel):
    """
    Base Model supporting timestamp and soft delete functionality.
    """

    class Meta:
        abstract = True
