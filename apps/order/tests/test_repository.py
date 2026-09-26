from uuid import uuid4

import pytest
from django.utils import timezone

from apps.order.repository import OrderRepository
from apps.order.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


def test_scoping(order):
    foreign = OrderFactory()
    OrderFactory(user=order.user, deleted_at=timezone.now())
    assert set(OrderRepository.get_order_queryset()) == {order, foreign}
    assert list(OrderRepository.get_user_orders(order.user)) == [order]
    assert list(OrderRepository.get_instructor_orders(order.instructor)) == [order]
    assert OrderRepository.get_order_by_id(order.pk) == order
    assert OrderRepository.get_order_by_id(uuid4()) is None


def test_create_update_lifecycle(order):
    created = OrderRepository.create_order(
        user=order.user, instructor=order.instructor, course=order.course
    )
    OrderRepository.update_order(created, status="success")
    created.refresh_from_db()
    assert created.status == "success"
    OrderRepository.soft_delete_order(created)
    assert OrderRepository.get_order_by_id(created.pk) is None
    OrderRepository.restore_order(created)
    assert OrderRepository.get_order_by_id(created.pk) == created
    assert OrderRepository.toggle_order_status(created) == "deleted"
