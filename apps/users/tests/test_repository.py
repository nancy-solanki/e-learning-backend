from uuid import uuid4

import pytest

from apps.users.repository import UserRepository
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_getters():
    user = UserFactory()
    assert UserRepository.get_user_by_id(user.pk) == user
    assert UserRepository.get_user_by_email(user.email) == user
    assert list(UserRepository.get_all_users()) == [user]


def test_missing_user():
    assert UserRepository.get_user_by_id(uuid4()) is None
    assert UserRepository.get_user_by_email("missing@example.com") is None
