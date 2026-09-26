import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.users.tests.factories import SuperuserFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def superuser(db):
    admin_group, _ = Group.objects.get_or_create(name="admin")
    su = SuperuserFactory()
    su.groups.add(admin_group)
    return su


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client
