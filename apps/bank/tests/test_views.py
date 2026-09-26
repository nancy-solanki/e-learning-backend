import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.bank.models import Bank
from apps.bank.tests.factories import BankFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestBankViewSet:
    def test_list_returns_user_banks(self, api_client, instructor_user):
        api_client.force_authenticate(user=instructor_user)
        BankFactory(
            user=instructor_user,
            name="Bank A",
            ifsc_code="BANK0001234",
            account_number="1212121212",
        )
        BankFactory(
            user=instructor_user,
            name="Bank B",
            ifsc_code="BANK0005678",
            account_number="1313131313",
        )

        response = api_client.get("/api/v1/bank/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        assert len(response.data["results"]) == 2

    def test_create_bank_sets_default_and_returns_201(
        self, api_client, instructor_user
    ):
        api_client.force_authenticate(user=instructor_user)
        payload = {
            "name": "Bank C",
            "ifsc_code": "BANK0009012",
            "account_number": "1414141414",
        }

        response = api_client.post("/api/v1/bank/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["default"] is True
        assert response.data["user"] == instructor_user.username

    def test_setting_default_via_patch_updates_default_bank(
        self, api_client, instructor_user
    ):
        api_client.force_authenticate(user=instructor_user)
        first = BankFactory(
            user=instructor_user,
            name="Alpha",
            ifsc_code="ALPH0001234",
            account_number="1515151515",
        )
        second = BankFactory(
            user=instructor_user,
            name="Beta",
            ifsc_code="BETA0001234",
            account_number="1616161616",
        )

        response = api_client.patch(
            f"/api/v1/bank/{second.id}/", {"default": True}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.default is False
        assert second.default is True
        assert response.data["message"] == "Account set successfully"

    def test_destroy_primary_bank_returns_validation_error(
        self, api_client, instructor_user
    ):
        api_client.force_authenticate(user=instructor_user)
        bank = BankFactory(
            user=instructor_user,
            name="Primary",
            ifsc_code="PRIM0001234",
            account_number="1717171717",
        )

        response = api_client.delete(f"/api/v1/bank/{bank.id}/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Primary Account can't be deleted" in str(response.data)

    def test_destroy_secondary_bank_returns_204(self, api_client, instructor_user):
        api_client.force_authenticate(user=instructor_user)
        first = BankFactory(
            user=instructor_user,
            name="Main",
            ifsc_code="MAIN0001234",
            account_number="1818181818",
        )
        second = BankFactory(
            user=instructor_user,
            name="Backup",
            ifsc_code="BACK0001234",
            account_number="1919191919",
        )
        first.default = False
        first.save(update_fields=["default"])

        response = api_client.delete(f"/api/v1/bank/{second.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        second.refresh_from_db()
        assert second.is_deleted is True


def detail(bank):
    return reverse("bank:bank-detail", kwargs={"pk": bank.pk})


def test_duplicate_account_rejected_by_api(client, bank):
    response = client.post(
        reverse("bank:bank-list"),
        {
            "name": "Other",
            "ifsc_code": "BANK0001234",
            "account_number": bank.account_number,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "account_number" in response.data
    assert Bank.objects.count() == 1


def test_create_ignores_supplied_owner(client, owner):
    other = UserFactory()
    response = client.post(
        reverse("bank:bank-list"),
        {
            "name": "Bank",
            "ifsc_code": "BANK0001234",
            "account_number": "1234567890",
            "user": str(other.pk),
        },
        format="json",
    )
    assert response.status_code == 201
    assert Bank.objects.get(pk=response.data["id"]).user == owner


@pytest.mark.parametrize("method", ["get", "patch", "put", "delete"])
def test_foreign_account_not_accessible(client, bank_factory, method):
    bank = bank_factory(user=UserFactory())
    response = getattr(client, method)(detail(bank))
    assert response.status_code == 404
    bank.refresh_from_db()
    assert bank.deleted_at is None


@pytest.mark.parametrize("method", ["get", "post", "patch", "put", "delete"])
def test_anonymous_denied(bank, method):
    url = reverse("bank:bank-list") if method in ("get", "post") else detail(bank)
    assert getattr(APIClient(), method)(url).status_code == 401


@pytest.mark.parametrize("method", ["post", "patch", "put", "delete"])
def test_student_cannot_write(bank, method):
    client = APIClient()
    client.force_authenticate(UserFactory())
    url = reverse("bank:bank-list") if method == "post" else detail(bank)
    assert getattr(client, method)(url).status_code == 403


def test_list_isolated_and_deleted_hidden(client, bank, bank_factory):
    bank_factory(user=UserFactory())
    deleted = bank_factory()
    deleted.soft_delete()
    response = client.get(reverse("bank:bank-list"))
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(bank.pk)]
    assert client.get(detail(deleted)).status_code == 404


def test_normal_update_persists_without_changing_owner(client, bank):
    response = client.patch(detail(bank), {"name": "Renamed"}, format="json")
    assert response.status_code == 200
    bank.refresh_from_db()
    assert bank.name == "Renamed"
    assert bank.default


def test_invalid_update_leaves_bank_unchanged(client, bank):
    old_name = bank.name
    response = client.patch(detail(bank), {"name": ""}, format="json")
    assert response.status_code == 400
    bank.refresh_from_db()
    assert bank.name == old_name


@pytest.mark.parametrize(
    "query, expected",
    [
        ({"default": "true"}, ["Alpha"]),
        ({"default": "false"}, ["Beta"]),
        ({"search": "Beta"}, ["Beta"]),
        ({"ordering": "name"}, ["Alpha", "Beta"]),
        ({"ordering": "-name"}, ["Beta", "Alpha"]),
    ],
)
def test_filters_and_ordering(client, bank_factory, query, expected):
    bank_factory(name="Alpha")
    bank_factory(name="Beta")
    response = client.get(reverse("bank:bank-list"), query)
    assert response.status_code == 200
    assert [row["name"] for row in response.data["results"]] == expected
