from datetime import date, timedelta

import pytest
from django.db import IntegrityError, transaction

from apps.coupon.tests.factories import CouponFactory

pytestmark = pytest.mark.django_db


def test_default_expiry_and_string(coupon):
    assert coupon.expired_at == date.today() + timedelta(days=3)
    assert str(coupon) == coupon.code


def test_explicit_expiry_preserved():
    expiry = date.today() + timedelta(days=7)
    coupon = CouponFactory(expired_at=expiry)
    coupon.save()
    coupon.refresh_from_db()
    assert coupon.expired_at == expiry


def test_unique_code(coupon):
    with pytest.raises(IntegrityError), transaction.atomic():
        CouponFactory(code=coupon.code)


def test_toggle_delete_and_restore(coupon):
    assert coupon.toggle_deleted() == "deleted"
    coupon.refresh_from_db()
    assert coupon.is_deleted
    assert coupon.toggle_deleted() == "activated"
    coupon.refresh_from_db()
    assert not coupon.is_deleted
