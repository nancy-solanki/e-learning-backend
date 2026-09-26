from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

from .manager import UserManager

# Create your models here.


class User(AbstractUser, BaseModel):

    class Status(models.TextChoices):
        ACTIVE = ("AC", "ACTIVE")
        PENDING = ("PD", "PENDING")
        SUSPEND = ("SA", "SUSPEND")
        INACTIVE = ("NA", "INACTIVE")

    class Gender(models.TextChoices):
        MALE = ("MA", "MALE")
        FEMALE = ("FE", "FEMALE")

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=200)
    last_name = models.CharField(_("last name"), max_length=200)
    username = models.CharField(_("username"), max_length=200, unique=True)
    avatar = models.URLField(_("avatar"), blank=True)
    phone_number = models.CharField(_("phone number"), max_length=15, blank=True)
    status = models.CharField(
        _("status"), max_length=2, choices=Status.choices, default=Status.PENDING
    )
    birth_date = models.DateField(_("birth date"), null=True, blank=True)
    gender = models.CharField(
        _("gender"), max_length=2, choices=Gender.choices, default=Gender.MALE
    )
    account_activity = models.BooleanField(_("account activity"), default=True)
    message_notifications = models.BooleanField(
        _("message notifications"), default=True
    )
    email_notifications = models.BooleanField(_("email notifications"), default=True)
    password_changed_at = models.DateTimeField(
        _("password changed at"), null=True, blank=True
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        self.username = self.username.lower()
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.is_superuser or self.groups.filter(name="admin").exists()

    @property
    def is_instructor(self):
        return self.groups.filter(name="instructor").exists()

    def become_instructor(self):
        from django.contrib.auth.models import Group

        self.groups.add(Group.objects.get_or_create(name="instructor")[0])

    def toggle_admin_privileges(self):
        from django.contrib.auth.models import Group

        group = Group.objects.get_or_create(name="admin")[0]
        if self.groups.filter(pk=group.pk).exists():
            self.groups.remove(group)
            return "removed from"
        self.groups.add(group)
        return "added to"

    def toggle_status(self):
        if self.status not in (self.Status.ACTIVE, self.Status.SUSPEND):
            raise ValueError("Only active or suspended users can change status.")
        self.status = (
            self.Status.SUSPEND
            if self.status == self.Status.ACTIVE
            else self.Status.ACTIVE
        )
        self.save(update_fields=["status"])
        return "activated" if self.status == self.Status.ACTIVE else "suspended"

    def __str__(self):
        return self.email

    class Meta:
        db_table = "user"
        verbose_name = "user"
        verbose_name_plural = "users"
        ordering = ["-created_at"]
