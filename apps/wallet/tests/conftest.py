import pytest
from rest_framework.test import APIClient

from apps.wallet.tests.factories import WalletFactory


@pytest.fixture
def wallet(db):
    return WalletFactory()


@pytest.fixture
def client():
    return APIClient()
