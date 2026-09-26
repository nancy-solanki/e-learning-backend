import pytest

from apps.order.models import Order
from apps.order.tests.factories import OrderFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/order/"


@pytest.mark.parametrize("role", ["user", "instructor"])
def test_lists_and_details_are_scoped(client, order, role):
    url = BASE + role + "/"
    assert client.get(url).status_code == 401
    client.force_authenticate(getattr(order, role))
    OrderFactory()
    response = client.get(url)
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(order.pk)
    assert client.get(url + f"{order.pk}/").status_code == 200
    client.force_authenticate(UserFactory())
    assert client.get(url + f"{order.pk}/").status_code == 404


def test_deleted_order_hidden(client, order):
    client.force_authenticate(order.user)
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
