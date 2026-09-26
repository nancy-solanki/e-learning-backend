import pytest
from rest_framework.test import APIClient

from apps.order.tests.factories import OrderFactory


@pytest.fixture
def order(db):
    return OrderFactory()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def gateway(mocker):
    client = mocker.patch("apps.order.service.razorpay.Client").return_value
    client.order.create.return_value = {"id": "order_test", "amount": 10000}
    client.utility.verify_payment_signature.return_value = True
    return client
