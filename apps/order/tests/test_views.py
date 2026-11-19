import pytest

from apps.order.models import Order
from apps.order.tests.factories import OrderFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/order/"


def test_order_list_and_detail_require_admin(client, order):
    url = BASE + "user/"
    assert client.get(url).status_code == 401
    client.force_authenticate(order.user)
    assert client.get(url).status_code == 403
    assert client.get(url + f"{order.pk}/").status_code == 403


def test_admin_uses_existing_user_order_endpoints_for_all_orders(client, order):
    from django.contrib.auth.models import Group

    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    another = OrderFactory()
    client.force_authenticate(admin)

    response = client.get(BASE + "user/")
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert client.get(BASE + f"user/{order.pk}/").status_code == 200
    assert client.get(BASE + f"user/{another.pk}/").status_code == 200


def test_instructor_cannot_access_order_list_or_detail(client, order):
    instructor = UserFactory()
    instructor.become_instructor()
    client.force_authenticate(instructor)
    assert client.get(BASE + "user/").status_code == 403
    assert client.get(BASE + f"user/{order.pk}/").status_code == 403


def test_deleted_order_hidden(client, order):
    from django.contrib.auth.models import Group

    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(admin)
    order.soft_delete()
    assert client.get(BASE + f"user/{order.pk}/").status_code == 404


@pytest.mark.parametrize("payload", [{}, {"total_paid": 100}, {"course": "missing"}])
def test_make_payment_required_fields(client, payload, gateway):
    client.force_authenticate(UserFactory())
    assert (
        client.post(BASE + "make-payment/", payload, format="json").status_code == 400
    )
    gateway.order.create.assert_not_called()


def test_make_payment_success_and_failure(client, order, gateway):
    client.force_authenticate(order.user)
    data = {"course": str(order.course_id), "total_paid": 100}
    assert client.post(BASE + "make-payment/", data, format="json").status_code == 201
    gateway.order.create.side_effect = RuntimeError("Unavailable")
    assert client.post(BASE + "make-payment/", data, format="json").status_code == 500
    client.force_authenticate(order.instructor)
    assert client.post(BASE + "make-payment/", data, format="json").status_code == 400


def test_success_payment_endpoint(client, order, gateway):
    client.force_authenticate(order.user)
    data = {
        "course": str(order.course_id),
        "total_paid": 100,
        "response": {
            "razorpay_order_id": "order_test",
            "razorpay_payment_id": "pay_test",
            "razorpay_signature": "signature",
        },
    }
    assert (
        client.post(BASE + "success-payment/", data, format="json").status_code == 200
    )
    assert Order.objects.filter(status="success").count() == 1
    assert (
        client.post(BASE + "success-payment/", data, format="json").status_code == 400
    )


@pytest.mark.parametrize("endpoint", ["make-payment", "success-payment"])
def test_payment_requires_auth(client, endpoint):
    assert client.post(BASE + endpoint + "/", {}).status_code == 401
