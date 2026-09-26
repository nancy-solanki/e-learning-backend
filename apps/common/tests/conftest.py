import pytest
from rest_framework.test import APIClient

from apps.common.tests.factories import FileFactory
from apps.course.models import Course
from apps.users.tests.factories import SuperuserFactory


@pytest.fixture
def dashboard_urls(settings):
    settings.ROOT_URLCONF = "apps.common.urls"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def admin(client, db):
    user = SuperuserFactory()
    client.force_authenticate(user)
    return user


@pytest.fixture
def course(admin):
    return Course.objects.create(
        title="Python",
        slug="python",
        instructor=admin,
        thumbnail=FileFactory(),
        short_description="Learn",
        long_description="Learn Python",
        learn_description_points="Basics",
        requirements="None",
    )
