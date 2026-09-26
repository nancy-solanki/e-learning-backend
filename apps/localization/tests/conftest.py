import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.localization.tests.factories import LocalizationFactory
from apps.users.tests.factories import UserFactory


@pytest.fixture
def instructor(db):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="instructor")[0])
    return user


@pytest.fixture
def localization(instructor):
    return LocalizationFactory()


@pytest.fixture
def client():
    return APIClient()
