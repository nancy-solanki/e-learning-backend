import pytest

from apps.coupon.serializers import CouponSerializer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "field, value",
    [
        ("code", ""),
        ("code", "x" * 101),
        ("coupon_type", "invalid"),
        ("expired_at", "not-a-date"),
    ],
)
def test_invalid_fields(course, field, value):
    data = {"code": "SAVE", "course": str(course.pk), field: value}
    serializer = CouponSerializer(data=data)
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_duplicate_code(coupon):
    serializer = CouponSerializer(
        data={"code": coupon.code, "course": str(coupon.course_id)}
    )
    assert not serializer.is_valid()
    assert "code" in serializer.errors


def test_course_title_representation(coupon):
    assert CouponSerializer(coupon).data["course_title"] == coupon.course.title
