import pytest
from django.contrib.auth.models import Group

from apps.transaction.tests.factories import TransactionFactory
from apps.users.tests.factories import UserFactory
from apps.wallet.models import Wallet

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


def test_admin_list_returns_all_active_transactions(client, transaction):
    url = BASE
    another = TransactionFactory()
    deleted = TransactionFactory()
    deleted.soft_delete()

    assert client.get(url).status_code == 401
    client.force_authenticate(transaction.user)
    personal_response = client.get(url)
    assert personal_response.status_code == 200
    assert personal_response.data["count"] == 1
    assert personal_response.data["results"][0]["id"] == str(transaction.pk)

    instructor = UserFactory()
    instructor.become_instructor()
    instructor_wallet = Wallet.objects.get(user=instructor)
    instructor_transaction = TransactionFactory(
        wallet=instructor_wallet, user=instructor
    )
    client.force_authenticate(instructor)
    instructor_response = client.get(url)
    assert instructor_response.status_code == 200
    assert instructor_response.data["count"] == 1
    assert instructor_response.data["results"][0]["id"] == str(
        instructor_transaction.pk
    )

    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(admin)
    response = client.get(url)
    assert response.status_code == 200
    assert response.data["count"] == 3
    assert {row["id"] for row in response.data["results"]} == {
        str(transaction.pk),
        str(another.pk),
        str(instructor_transaction.pk),
    }
    assert {row["user"]["id"] for row in response.data["results"]} == {
        str(transaction.user_id),
        str(another.user_id),
        str(instructor.pk),
    }


def test_admin_list_supports_existing_filters(client, transaction):
    other = TransactionFactory(status="failed", transaction_type="debit")
    admin = UserFactory(is_superuser=True)
    client.force_authenticate(admin)

    response = client.get(BASE, {"status": "failed"})
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(other.pk)


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
