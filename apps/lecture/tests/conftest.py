import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.lecture.tests.factories import LectureFactory
from apps.users.tests.factories import UserFactory


@pytest.fixture
def instructor(db):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="instructor")[0])
    return user


@pytest.fixture
def lecture(instructor):
    return LectureFactory(section__course__instructor=instructor)


@pytest.fixture
def client():
    return APIClient()
