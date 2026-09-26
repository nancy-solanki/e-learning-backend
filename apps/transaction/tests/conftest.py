import pytest
from rest_framework.test import APIClient

from apps.transaction.tests.factories import TransactionFactory


@pytest.fixture
def transaction(db):
    return TransactionFactory()


@pytest.fixture
def client():
    return APIClient()
