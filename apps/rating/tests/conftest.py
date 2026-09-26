import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.course.tests.factories import CourseFactory
from apps.rating.tests.factories import RatingFactory
from apps.users.tests.factories import UserFactory


@pytest.fixture
def instructor(db):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="instructor")[0])
    return user


@pytest.fixture
def course(instructor):
    return CourseFactory(instructor=instructor)


@pytest.fixture
def rating(course):
    return RatingFactory(course=course)


@pytest.fixture
def client():
    return APIClient()
