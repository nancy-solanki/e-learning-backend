from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.user.manager import UserManager

# Create your models here.


class User(AbstractUser, BaseModel):

    class Status(models.TextChoices):
        ACTIVE = ("AC", "ACTIVE")
        PENDING = ("PD", "PENDING")
        INACTIVE = ("NA", "INACTIVE")

    class Gender(models.TextChoices):
        MALE = ("MA", "MALE")
        FEMALE = ("FE", "FEMALE")

    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=200)
    last_name = models.CharField(_('last name'), max_length=200)
    username = models.CharField(_('username'), max_length=200, unique=True)
    profile_picture = models.URLField(_('profile_picture'), blank=True)
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    status = models.CharField(
        _('status'),
        max_length=2,
        choices=Status.choices,
        default=Status.PENDING
    )
    birth_date = models.DateField(_('birth date'), null=True, blank=True)
    gender = models.CharField(
        _('gender'),
        max_length=2,
        choices=Gender.choices,
        default=Gender.MALE
    )
    message_notifications = models.BooleanField(_('message notifications'), default=True)
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    password_changed_at = models.DateTimeField(_('password changed at'), null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        self.username = self.username.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'user'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ["-created_at"]
