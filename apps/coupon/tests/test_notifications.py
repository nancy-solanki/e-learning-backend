from datetime import timedelta

import pytest
from django.utils import timezone

from apps.coupon.tasks import notify_expiring_coupons
from apps.coupon.tests.factories import CouponFactory
from apps.enroll.models import Enroll
from apps.users.models import User
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_coupon_notifications_only_target_promotional_opt_ins(mocker, coupon):
    opted_in = UserFactory(
        status=User.Status.ACTIVE,
        is_active=True,
        promotional_emails=True,
    )
    Enroll.objects.create(user=opted_in, course=coupon.course)
    UserFactory(
        status=User.Status.ACTIVE,
        is_active=True,
        promotional_emails=True,
    )
    UserFactory(
        status=User.Status.ACTIVE,
        is_active=True,
        promotional_emails=False,
    )
    queue_email = mocker.patch(
        "apps.coupon.email_notifications.queue_notification_email"
    )

    from apps.coupon.email_notifications import notify_coupon_audience

    notify_coupon_audience(coupon, event="created")

    queue_email.assert_called_once()
    assert queue_email.call_args.args[0] == opted_in
    assert queue_email.call_args.kwargs["preference_field"] == "promotional_emails"


def test_coupon_expiry_notification_is_recorded_and_sent_once(mocker):
    coupon = CouponFactory(expired_at=timezone.localdate() + timedelta(days=1))
    notify = mocker.patch("apps.coupon.tasks.notify_coupon_audience")

    assert notify_expiring_coupons.run() == 1
    coupon.refresh_from_db()
    assert coupon.expiry_notified_at is not None
    notify.assert_called_once_with(coupon, event="expiring")

    assert notify_expiring_coupons.run() == 0
    notify.assert_called_once()


def test_expired_or_deleted_coupons_are_not_announced(mocker):
    expired = CouponFactory(expired_at=timezone.localdate())
    deleted = CouponFactory(expired_at=timezone.localdate() + timedelta(days=1))
    deleted.soft_delete()
    notify = mocker.patch("apps.coupon.tasks.notify_coupon_audience")

    assert notify_expiring_coupons.run() == 0
    expired.refresh_from_db()
    deleted.refresh_from_db()
    assert expired.expiry_notified_at is None
    assert deleted.expiry_notified_at is None
    notify.assert_not_called()
