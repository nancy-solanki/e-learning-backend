import pytest
from rest_framework.test import APIClient

from apps.enroll.tests.factories import EnrollFactory


@pytest.fixture
def enroll(db):
    return EnrollFactory()


@pytest.fixture
def client():
    return APIClient()
