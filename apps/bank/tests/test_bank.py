import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.bank.models import Bank
from apps.bank.repository import BankRepository
from apps.bank.service import BankService
from apps.users.tests.factories import UserFactory

User = get_user_model()


@pytest.fixture
def instructor_user(db):
    user = UserFactory()
    group, _ = Group.objects.get_or_create(name="instructor")
    user.groups.add(group)
    return user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestBankModel:
    def test_first_bank_is_default(self):
        user = UserFactory()
        bank = Bank.objects.create(
            user=user,
            name="SBI",
            ifsc_code="SBIN0001234",
            account_number="1234567890",
        )

        assert bank.default is True

    def test_second_bank_is_not_default_by_default(self):
        user = UserFactory()
        Bank.objects.create(
            user=user,
            name="HDFC",
            ifsc_code="HDFC0001234",
            account_number="1111111111",
        )
        second = Bank.objects.create(
            user=user,
            name="ICICI",
            ifsc_code="ICIC0001234",
            account_number="2222222222",
        )

        assert second.default is False

    def test_bank_soft_delete_restore_and_toggle(self):
        user = UserFactory()
        bank = Bank.objects.create(
            user=user,
            name="Axis",
            ifsc_code="UTIB0001234",
            account_number="3333333333",
        )

        bank.soft_delete()
        assert bank.is_deleted is True

        bank.restore()
        assert bank.is_deleted is False

        assert bank.toggle_deleted().is_deleted is True
        assert bank.toggle_deleted().is_deleted is False


@pytest.mark.django_db
class TestBankRepository:
    def test_repository_getters_and_create(self):
        user = UserFactory()
        bank = BankRepository.create_bank(
            user=user,
            name="Kotak",
            ifsc_code="KKBK0001234",
            account_number="4444444444",
        )

        assert BankRepository.get_bank_by_id(bank.id) == bank
        assert list(BankRepository.get_banks_by_user(user)) == [bank]
        assert BankRepository.get_default_bank(user) == bank
        assert BankRepository.get_all_banks().count() == 1

        saved = BankRepository.save(bank)
        assert saved == bank


@pytest.mark.django_db
class TestBankService:
    def test_set_default_bank_updates_default_flag(self):
        user = UserFactory()
        first = Bank.objects.create(
            user=user,
            name="PNB",
            ifsc_code="PUNB0001234",
            account_number="5555555555",
        )
        second = Bank.objects.create(
            user=user,
            name="Yes Bank",
            ifsc_code="YESB0001234",
            account_number="6666666666",
        )

        message = BankService.set_default_bank(user, second.id)

        first.refresh_from_db()
        second.refresh_from_db()
        assert message == "Account set successfully"
        assert first.default is False
        assert second.default is True

    def test_set_default_bank_rejects_unknown_or_foreign_account(self):
        user = UserFactory()
        other_user = UserFactory()
        bank = Bank.objects.create(
            user=other_user,
            name="BOI",
            ifsc_code="BKID0001234",
            account_number="7777777777",
        )

        with pytest.raises(
            ValidationError, match="Bank not found or not owned by user"
        ):
            BankService.set_default_bank(user, bank.id)

        with pytest.raises(
            ValidationError, match="Bank not found or not owned by user"
        ):
            BankService.set_default_bank(user, "00000000-0000-0000-0000-000000000000")

    def test_toggle_delete_bank_rejects_primary_account_delete(self):
        user = UserFactory()
        bank = Bank.objects.create(
            user=user,
            name="Federal",
            ifsc_code="SBIN0005678",
            account_number="8888888888",
        )

        with pytest.raises(ValidationError, match="Primary Account can't be deleted"):
            BankService.toggle_delete_bank(bank)

    def test_toggle_delete_bank_for_secondary_account(self):
        user = UserFactory()
        Bank.objects.create(
            user=user,
            name="IDBI",
            ifsc_code="IDIB0001234",
            account_number="9999999999",
        )
        second = Bank.objects.create(
            user=user,
            name="Canara",
            ifsc_code="CNRB0001234",
            account_number="1010101010",
        )
        second.default = False
        second.save(update_fields=["default"])

        assert BankService.toggle_delete_bank(second) == "Deleted successfully"
        second.refresh_from_db()
        assert second.is_deleted is True

        assert BankService.toggle_delete_bank(second) == "Activated successfully"
        second.refresh_from_db()
        assert second.is_deleted is False


@pytest.mark.django_db
class TestBankViewSet:
    def test_list_returns_user_banks(self, api_client, instructor_user):
        api_client.force_authenticate(user=instructor_user)
        Bank.objects.create(
            user=instructor_user,
            name="Bank A",
            ifsc_code="BANK0001234",
            account_number="1212121212",
        )
        Bank.objects.create(
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
        first = Bank.objects.create(
            user=instructor_user,
            name="Alpha",
            ifsc_code="ALPH0001234",
            account_number="1515151515",
        )
        second = Bank.objects.create(
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
        bank = Bank.objects.create(
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
        first = Bank.objects.create(
            user=instructor_user,
            name="Main",
            ifsc_code="MAIN0001234",
            account_number="1818181818",
        )
        second = Bank.objects.create(
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
