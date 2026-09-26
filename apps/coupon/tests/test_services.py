from datetime import date, timedelta

import pytest
from django.contrib.auth.models import Group

from apps.coupon.service import CouponService
from apps.coupon.tests.factories import CouponFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "days, used, limit, unlimited, error",
    [
        (1, 0, 10, False, None),
        (0, 0, 10, False, None),
        (-1, 0, 10, False, "Coupon has expired!"),
        (1, 10, 10, False, "Coupon usage limit reached!"),
        (1, 11, 10, False, "Coupon usage limit reached!"),
        (1, 100, 0, True, None),
        (-1, 100, 0, True, "Coupon has expired!"),
    ],
)
def test_validation_boundaries(days, used, limit, unlimited, error):
    coupon = CouponFactory(
        expired_at=date.today() + timedelta(days=days),
        used=used,
        limit=limit,
        is_unlimited=unlimited,
    )
    result, message = CouponService.validate_coupon(coupon.code)
    assert message == error
    assert result == (None if error else coupon)


def test_missing_and_deleted_coupon(coupon):
    assert CouponService.validate_coupon("unknown") == (None, "Coupon not found!")
    coupon.soft_delete()
    assert CouponService.validate_coupon(coupon.code) == (None, "Coupon not found!")


def test_role_scoping(coupon, instructor):
    foreign = CouponFactory()
    assert list(CouponService.get_coupons(instructor)) == [coupon]
    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    assert set(CouponService.get_coupons(admin)) == {coupon, foreign}


def test_toggle_messages(coupon):
    assert CouponService.toggle_coupon_status(coupon) == "Coupon deleted successfully"
    assert CouponService.toggle_coupon_status(coupon) == "Coupon activated successfully"
