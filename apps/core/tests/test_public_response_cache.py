import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.course.models import Course

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