import pytest

pytestmark = pytest.mark.django_db


def test_soft_delete_and_restore(order):
    order.soft_delete()
    order.refresh_from_db()
    assert order.is_deleted
    order.restore()
    order.refresh_from_db()
    assert not order.is_deleted


def test_string(order):
    assert str(order) == str(order.user)


def test_toggle(order):
    assert order.toggle_deleted() == "deleted"
    order.refresh_from_db()
    assert order.is_deleted
    assert order.toggle_deleted() == "activated"
    order.refresh_from_db()
    assert not order.is_deleted
