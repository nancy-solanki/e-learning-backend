import pytest

from apps.enroll.serializers import EnrollSerializer

pytestmark = pytest.mark.django_db


def test_nested_representation(enroll):
    enroll.average_rating = 4.5
    data = EnrollSerializer(enroll).data
    assert data["user"]["id"] == str(enroll.user_id)
    assert data["course"]["id"] == str(enroll.course_id)
    assert data["average_rating"] == 4.5
    assert data["progress"] == 0
    assert "password" not in data["user"]
