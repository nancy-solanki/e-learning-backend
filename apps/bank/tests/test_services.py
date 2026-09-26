import pytest
from rest_framework.exceptions import ValidationError

from apps.bank.models import Bank
from apps.bank.service import BankService
from apps.bank.tests.factories import BankFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestBankService:
    def test_set_default_bank_updates_default_flag(self):
        user = UserFactory()
        first = BankFactory(
            user=user,
            name="PNB",
            ifsc_code="PUNB0001234",
            account_number="5555555555",
        )
        second = BankFactory(
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
        bank = BankFactory(
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
        bank = BankFactory(
            user=user,
            name="Federal",
            ifsc_code="SBIN0005678",
            account_number="8888888888",
        )

        with pytest.raises(ValidationError, match="Primary Account can't be deleted"):
            BankService.toggle_delete_bank(bank)

    def test_toggle_delete_bank_for_secondary_account(self):
        user = UserFactory()
        BankFactory(
            user=user,
            name="IDBI",
            ifsc_code="IDIB0001234",
            account_number="9999999999",
        )
        second = BankFactory(
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


def test_cannot_select_deleted_default(bank, owner):
    bank.soft_delete()
    with pytest.raises(ValidationError):
        BankService.set_default_bank(owner, bank.pk)


def test_select_default_without_current_default(bank, bank_factory, owner):
    bank.default = False
    bank.save()
    second = bank_factory()
    BankService.set_default_bank(owner, second.pk)
    second.refresh_from_db()
    assert second.default
    assert Bank.objects.filter(user=owner, default=True).count() == 1


def test_selecting_default_again_is_idempotent(bank, owner):
    BankService.set_default_bank(owner, bank.pk)
    BankService.set_default_bank(owner, bank.pk)
    bank.refresh_from_db()
    assert bank.default
    assert Bank.objects.filter(user=owner, default=True).count() == 1
