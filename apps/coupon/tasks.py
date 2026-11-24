from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from config.celery import celery_app

from .email_notifications import notify_coupon_audience
from .models import Coupon


@celery_app.task
def notify_expiring_coupons() -> int:
    today = timezone.localdate()
    reminder_deadline = today + timedelta(days=1)
    coupon_ids = Coupon.objects.filter(
        deleted_at__isnull=True,
        expired_at__gt=today,
        expired_at__lte=reminder_deadline,
        expiry_notified_at__isnull=True,
    ).values_list("pk", flat=True)

    notified = 0
    for coupon_id in coupon_ids.iterator(chunk_size=500):
        with transaction.atomic():
            coupon = (
                Coupon.objects.select_for_update()
                .filter(
                    pk=coupon_id,
                    deleted_at__isnull=True,
                    expiry_notified_at__isnull=True,
                )
                .first()
            )
            if coupon is None:
                continue
            coupon.expiry_notified_at = timezone.now()
            coupon.save(update_fields=("expiry_notified_at", "updated_at"))
            notify_coupon_audience(coupon, event="expiring")
            notified += 1
    return notified
