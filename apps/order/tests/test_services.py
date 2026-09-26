import json
from uuid import uuid4

import pytest
from django.contrib.auth.models import Group

from apps.coupon.tests.factories import CouponFactory
from apps.course.tests.factories import CourseFactory
from apps.enroll.models import Enroll
from apps.order.models import Order
from apps.order.service import OrderService
from apps.users.tests.factories import UserFactory
from apps.wallet.tests.factories import WalletFactory

pytestmark = pytest.mark.django_db


def payload(course):
    return {
        "course": str(course.pk),
        "total_paid": 100,
        "response": {
            "razorpay_order_id": "order_test",
            "razorpay_payment_id": "pay_test",
            "razorpay_signature": "signature",
        },
    }


def test_create_gateway_order(gateway):
    course = CourseFactory()
    assert (
        OrderService.create_razorpay_order(100, course.pk, UserFactory())["id"]
        == "order_test"
    )
    gateway.order.create.assert_called_once_with(
        {"amount": 10000, "currency": "INR", "payment_capture": "1"}
    )


@pytest.mark.parametrize("case", ["missing", "owner", "enrolled"])
def test_create_rejects_ineligible(gateway, case):
    course = CourseFactory()
    user = course.instructor if case == "owner" else UserFactory()
    if case == "enrolled":
        Enroll.objects.create(user=user, course=course)
    with pytest.raises(ValueError):
        OrderService.create_razorpay_order(
            100, uuid4() if case == "missing" else course.pk, user
        )
    gateway.order.create.assert_not_called()


@pytest.mark.parametrize("as_json", [False, True])
def test_success_updates_records_and_wallets(gateway, as_json):
    course = CourseFactory()
    user = UserFactory()
    coupon = CouponFactory(course=course)
    site = WalletFactory(user=None, is_site_wallet=True)
    instructor = WalletFactory(user=course.instructor)
    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    admin_wallet = WalletFactory(user=admin)
    data = payload(course)
    data["coupon"] = str(coupon.pk)
    if as_json:
        data["response"] = json.dumps(data["response"])
    assert OrderService.process_successful_payment(data, user) == (
        True,
        "Payment success",
    )
    order = Order.objects.get()
    assert order.status == "success" and order.admin_commission == 10
    assert order.enroll.user == user and order.enroll.course == course
    for wallet, expected in [(site, 100), (instructor, 90), (admin_wallet, 10)]:
        wallet.refresh_from_db()
        assert wallet.current_earnings == expected
        assert wallet.total_earnings == expected
    coupon.refresh_from_db()
    assert coupon.used == 1
    gateway.utility.verify_payment_signature.assert_called_once()


@pytest.mark.parametrize("failure", [None, False, "exception", "json"])
def test_verification_failure_has_no_side_effects(gateway, failure):
    course = CourseFactory()
    coupon = CouponFactory(course=course)
    wallet = WalletFactory(user=course.instructor)
    data = payload(course)
    data["coupon"] = str(coupon.pk)
    if failure == "exception":
        gateway.utility.verify_payment_signature.side_effect = RuntimeError(
            "Invalid signature"
        )
    elif failure == "json":
        data["response"] = "invalid-json"
    else:
        gateway.utility.verify_payment_signature.return_value = failure
    assert OrderService.process_successful_payment(data, UserFactory())[0] is False
    assert not Order.objects.exists()
    assert not Enroll.objects.exists()
    coupon.refresh_from_db()
    wallet.refresh_from_db()
    assert coupon.used == 0
    assert wallet.current_earnings == 0


def test_free_course_skips_gateway(gateway):
    course = CourseFactory(is_free=True, price=0)
    data = {"course": str(course.pk), "total_paid": 0, "is_free": True}
    assert OrderService.process_successful_payment(data, UserFactory())[0]
    assert Order.objects.get().is_free
    gateway.utility.verify_payment_signature.assert_not_called()


def test_paid_course_cannot_bypass_verification(gateway):
    course = CourseFactory(is_free=False)
    data = {"course": str(course.pk), "total_paid": 0, "is_free": True}
    assert not OrderService.process_successful_payment(data, UserFactory())[0]
    assert not Enroll.objects.exists()


@pytest.mark.parametrize(
    "data",
    [{}, {"total_paid": "invalid", "course": "x"}, {"total_paid": -1, "course": "x"}],
)
def test_invalid_payment_data(data):
    assert not OrderService.process_successful_payment(data, UserFactory())[0]
    assert not Order.objects.exists()


def test_missing_course(gateway):
    assert OrderService.process_successful_payment(
        {"total_paid": 100, "course": str(uuid4())}, UserFactory()
    ) == (False, "Course not found")


def test_repeat_success_does_not_credit_twice(gateway):
    course = CourseFactory()
    user = UserFactory()
    assert OrderService.process_successful_payment(payload(course), user)[0]
    assert not OrderService.process_successful_payment(payload(course), user)[0]
    assert Order.objects.count() == Enroll.objects.count() == 1


def test_database_failure_rolls_back(gateway, mocker):
    course = CourseFactory()
    coupon = CouponFactory(course=course)
    data = payload(course)
    data["coupon"] = str(coupon.pk)
    mocker.patch(
        "apps.order.service.EnrollRepository.create_enrollment",
        side_effect=RuntimeError("Database failure"),
    )
    with pytest.raises(RuntimeError):
        OrderService.process_successful_payment(data, UserFactory())
    assert not Order.objects.exists()
    coupon.refresh_from_db()
    assert coupon.used == 0
