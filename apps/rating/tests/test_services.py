import pytest

from apps.rating.service import RatingService
from apps.rating.tests.factories import RatingFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_role_scoping(rating, instructor):
    foreign = RatingFactory()
    assert list(RatingService.get_ratings(instructor)) == [rating]
    assert set(RatingService.get_ratings(UserFactory())) == {rating, foreign}
    assert list(RatingService.get_instructor_course_ratings(instructor)) == [rating]


def test_add_rating(course):
    user = UserFactory()
    data = {"course": course, "rating": 4, "comment": "Good"}
    rating = RatingService.add_rating(user, data)
    rating.refresh_from_db()
    assert rating.user == user
    assert rating.course == course
    assert rating.comment == "Good"
    assert "user" not in data
