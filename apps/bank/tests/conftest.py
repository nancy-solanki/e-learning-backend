from functools import partial

import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.bank.tests.factories import BankFactory
from apps.users.tests.factories import UserFactory


@pytest.fixture
def instructor_user(db):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="instructor")[0])
    return user


@pytest.fixture
def owner(instructor_user):
    return instructor_user


@pytest.fixture
def bank_factory(owner):
    return partial(BankFactory, user=owner)


@pytest.fixture
def bank(bank_factory):
    return bank_factory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client(api_client, owner):
    api_client.force_authenticate(owner)
    return api_client
