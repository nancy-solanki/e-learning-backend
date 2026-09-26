import pytest

from apps.rating.repository import RatingRepository
from apps.rating.tests.factories import RatingFactory

pytestmark = pytest.mark.django_db


def test_scope_and_deleted_exclusion(rating, instructor, course):
    foreign = RatingFactory()
    deleted = RatingFactory(course=course)
    deleted.soft_delete()
    assert set(RatingRepository.get_all_ratings()) == {rating, foreign}
    assert list(RatingRepository.get_instructor_ratings(instructor)) == [rating]
    assert list(RatingRepository.get_course_ratings(course.pk)) == [rating]


def test_create_and_save(rating):
    created = RatingRepository.create_rating(
        rating.user, course=rating.course, rating=3, comment="Good"
    )
    created.comment = "Updated"
    assert RatingRepository.save(created) == created
    created.refresh_from_db()
    assert created.comment == "Updated"
