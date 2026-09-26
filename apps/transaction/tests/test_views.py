import pytest

from apps.transaction.tests.factories import TransactionFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/transaction/"


def test_list_detail_ownership(client, transaction):
    assert client.get(BASE).status_code == 401
    assert client.get(BASE + f"{transaction.pk}/").status_code == 401
    TransactionFactory()
    client.force_authenticate(transaction.user)
    response = client.get(BASE)
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(transaction.pk)
    assert client.get(BASE + f"{transaction.pk}/").status_code == 200
    client.force_authenticate(UserFactory())
    assert client.get(BASE + f"{transaction.pk}/").status_code == 404


def test_deleted_hidden(client, transaction):
    transaction.soft_delete()
    client.force_authenticate(transaction.user)
    assert client.get(BASE).data["count"] == 0
    assert client.get(BASE + f"{transaction.pk}/").status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_readonly(client, transaction, method):
    client.force_authenticate(transaction.user)
    target = BASE if method == "post" else BASE + f"{transaction.pk}/"
    assert getattr(client, method)(target).status_code == 405
