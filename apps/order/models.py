from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel

# Create your models here.


class Order(BaseModel):
    class STATUS(models.TextChoices):
        SUCCESS = ("success", "Success")
        REJECTED = ("rejected", "Rejected")
        PENDING = ("pending", "Pending")

    is_free = models.BooleanField(default=False)
    admin_commission = models.FloatField(default=0)
    status = models.CharField(
        max_length=9, choices=STATUS.choices, default=STATUS.PENDING
    )
    reject_reason = models.TextField(null=True, blank=True)
    total_paid = models.FloatField(default=0)
    user = models.ForeignKey(
        "users.User", on_delete=models.RESTRICT, related_name="orders"
    )
    instructor = models.ForeignKey(
        "users.User", on_delete=models.RESTRICT, related_name="instructor_orders"
    )
    course = models.ForeignKey("course.Course", on_delete=models.RESTRICT)
    coupon = models.ForeignKey(
        "coupon.Coupon", on_delete=models.RESTRICT, null=True, blank=True
    )
    enroll = models.ForeignKey(
        "enroll.Enroll",
        on_delete=models.RESTRICT,
        related_name="order_enroll",
        null=True,
        blank=True,
    )

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])
        return self

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
        return self

    def toggle_deleted(self) -> str:
        if self.is_deleted:
            self.restore()
            return "activated"
        self.soft_delete()
        return "deleted"

    def __str__(self):
        return str(self.user)

    class Meta:
        db_table = "order"
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ("-created_at",)
