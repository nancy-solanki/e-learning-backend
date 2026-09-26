from uuid import uuid4

import pytest

from apps.bank.repository import BankRepository
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


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


def test_repository_excludes_deleted(bank, owner):
    bank.soft_delete()
    assert BankRepository.get_bank_by_id(bank.pk) is None
    assert BankRepository.get_default_bank(owner) is None
    assert not BankRepository.get_banks_by_user(owner).exists()
    assert not BankRepository.get_all_banks().exists()
    assert BankRepository.get_bank_by_id(uuid4()) is None
