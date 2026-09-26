import pytest

from apps.coupon.repository import CouponRepository
from apps.coupon.tests.factories import CouponFactory

pytestmark = pytest.mark.django_db


def test_scope_and_soft_deletion(coupon, instructor, course):
    foreign = CouponFactory()
    admin_created = CouponFactory(course=course, is_instructor_created=False)
    deleted = CouponFactory(course=course)
    deleted.soft_delete()
    assert list(CouponRepository.get_instructor_coupons(instructor)) == [coupon]
    assert set(CouponRepository.get_active_coupons()) == {
        coupon,
        foreign,
        admin_created,
    }
    assert set(CouponRepository.get_all_coupons()) == {
        coupon,
        foreign,
        admin_created,
        deleted,
    }
    assert CouponRepository.get_coupon_by_code(coupon.code) == coupon
    assert CouponRepository.get_coupon_by_code(deleted.code) is None
    assert CouponRepository.get_coupon_by_code("missing") is None


def test_create_and_save(course):
    coupon = CouponRepository.create_coupon(code="SAVE", course=course)
    coupon.value = 20
    assert CouponRepository.save(coupon) == coupon
    coupon.refresh_from_db()
    assert coupon.value == 20
