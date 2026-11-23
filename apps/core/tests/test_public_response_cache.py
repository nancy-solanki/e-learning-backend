import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.course.models import Course
from apps.course.tests.factories import CourseFactory

pytestmark = pytest.mark.django_db


def test_public_course_list_uses_cached_response(mocker):
    cache.clear()
    get_public_queryset = mocker.patch(
        "apps.course.views.CourseService.get_public_queryset",
        return_value=Course.objects.none(),
    )
    client = APIClient()

    first_response = client.get("/api/v1/course/")
    second_response = client.get("/api/v1/course/")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.data == second_response.data
    get_public_queryset.assert_called_once()
    cache.clear()


def test_public_cache_is_invalidated_after_content_changes(mocker):
    cache.clear()
    get_public_queryset = mocker.patch(
        "apps.course.views.CourseService.get_public_queryset",
        return_value=Course.objects.none(),
    )
    client = APIClient()

    client.get("/api/v1/course/")
    CourseFactory(status="published")
    response = client.get("/api/v1/course/")

    assert response.status_code == 200
    assert get_public_queryset.call_count == 2
    cache.clear()