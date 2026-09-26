import pytest

from apps.bank.serializers import BankSerializer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("field", ["name", "ifsc_code", "account_number"])
@pytest.mark.parametrize("value", [None, "", "x" * 201])
def test_invalid_fields(field, value):
    data = {"name": "Bank", "ifsc_code": "BANK0001234", "account_number": "1234567890"}
    data[field] = value
    serializer = BankSerializer(data=data)
    assert not serializer.is_valid()
    assert field in serializer.errors


@pytest.mark.parametrize("field", ["name", "ifsc_code", "account_number"])
def test_missing_fields(field):
    data = {"name": "Bank", "ifsc_code": "BANK0001234", "account_number": "1234567890"}
    del data[field]
    serializer = BankSerializer(data=data)
    assert not serializer.is_valid()
    assert field in serializer.errors
