from datetime import date, timedelta

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

COUPON_TYPE = (("percentage", "Percentage"), ("fixed", "Fixed"))


class Coupon(BaseModel):
    code = models.CharField(max_length=100, unique=True)
    is_global = models.BooleanField(default=False)
    is_unlimited = models.BooleanField(default=False)
    is_instructor_created = models.BooleanField(default=True)
    limit = models.IntegerField(default=10)
    value = models.IntegerField(default=10)
    used = models.IntegerField(default=0)
    coupon_type = models.CharField(
        max_length=15, choices=COUPON_TYPE, default="percentage"
    )
    course = models.ForeignKey("course.Course", on_delete=models.RESTRICT)
    expired_at = models.DateField(default=None, null=True)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if self.expired_at is None:
            self.expired_at = date.today() + timedelta(days=3)
        super(Coupon, self).save(*args, **kwargs)

    def soft_delete(self):
        from django.utils import timezone

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

    class Meta:
        db_table = "coupon"
        verbose_name = _("coupon")
        verbose_name_plural = _("coupons")
        ordering = ["-created_at"]
