import pytest
from django.urls import reverse

from apps.enroll.models import Enroll
from apps.rating.models import Rating
from apps.rating.tests.factories import RatingFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def url(rating=None):
    if rating:
        return reverse("rating:rating-management-detail", kwargs={"pk": rating.pk})
    return reverse("rating:rating-management-list")


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
def test_anonymous_denied(client, rating, method):
    target = url() if method in ("get", "post") else url(rating)
    assert getattr(client, method)(target).status_code == 401


def test_create_returns_persisted_representation(client, course):
    user = UserFactory()
    Enroll.objects.create(user=user, course=course)
    client.force_authenticate(user)
    payload = {"course": str(course.pk), "rating": "4.0", "comment": "Good"}
    response = client.post(url(), payload, format="json")
    assert response.status_code == 201, response.data
    rating = Rating.objects.get(pk=response.data["id"])
    assert rating.user == user
    assert response.data["user"]["id"] == str(user.pk)
    assert response.data["course_title"] == course.title
    assert client.post(url(), payload, format="json").status_code == 400
    assert Rating.objects.count() == 1


def test_unenrolled_user_cannot_create(client, course):
    client.force_authenticate(UserFactory())
    response = client.post(
        url(), {"course": str(course.pk), "rating": 4, "comment": "Good"}
    )
    assert response.status_code == 400
    assert not Rating.objects.exists()


def test_owner_updates_and_soft_deletes(client, rating):
    client.force_authenticate(rating.user)
    assert (
        client.patch(url(rating), {"comment": "Updated"}, format="json").status_code
        == 200
    )
    rating.refresh_from_db()
    assert rating.comment == "Updated"
    assert client.delete(url(rating)).status_code == 204
    rating.refresh_from_db()
    assert rating.is_deleted
    assert client.get(url(rating)).status_code == 404


def test_instructor_can_only_reply(client, rating, instructor):
    client.force_authenticate(instructor)
    assert (
        client.patch(url(rating), {"response": "Thanks"}, format="json").status_code
        == 200
    )
    assert client.patch(url(rating), {"rating": 5}, format="json").status_code == 400
    rating.refresh_from_db()
    assert rating.response == "Thanks"
    assert rating.rating == 4


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_stranger_cannot_modify(client, rating, method):
    client.force_authenticate(UserFactory())
    assert getattr(client, method)(url(rating)).status_code == 403


def test_instructor_lists_only_own_courses(client, rating, instructor):
    RatingFactory()
    client.force_authenticate(instructor)
    response = client.get(url())
    assert [row["id"] for row in response.data["results"]] == [str(rating.pk)]
    response = client.get(reverse("rating:rating-by-instructor"))
    assert [row["id"] for row in response.data] == [str(rating.pk)]


def test_search(client, rating):
    RatingFactory(comment="Unrelated")
    client.force_authenticate(rating.user)
    response = client.get(url(), {"search": "Helpful"})
    assert [row["id"] for row in response.data["results"]] == [str(rating.pk)]
