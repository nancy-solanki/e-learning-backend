import pytest

from apps.order.serializers import OrderSerializer

pytestmark = pytest.mark.django_db


def test_nested_representation(order):
    data = OrderSerializer(order).data
    assert data["user"]["id"] == str(order.user_id)
    assert data["instructor"]["id"] == str(order.instructor_id)
    assert data["course"]["id"] == str(order.course_id)
    assert "password" not in data["user"]


@pytest.mark.parametrize(
    "field,value", [("status", "invalid"), ("total_paid", "invalid")]
)
def test_invalid_update(order, field, value):
    serializer = OrderSerializer(order, data={field: value}, partial=True)
    assert not serializer.is_valid()
    assert field in serializer.errors
