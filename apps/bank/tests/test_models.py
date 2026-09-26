import pytest
from django.db import IntegrityError, transaction

from apps.bank.models import Bank
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


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


def test_bank_string(bank):
    assert str(bank) == bank.name


def test_account_number_unique_in_database(bank, bank_factory):
    with pytest.raises(IntegrityError), transaction.atomic():
        bank_factory(account_number=bank.account_number)
