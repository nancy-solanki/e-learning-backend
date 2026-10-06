from datetime import datetime, timezone

import pytest
from django.urls import reverse

from apps.rating.tests.factories import RatingFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(params=["rating:rating-management-list", "rating:rating-by-instructor"])
def ratings(request, client, instructor):
    matched = RatingFactory(
        course__instructor=instructor,
        course__title="Unique Python Course",
        user__first_name="Alice",
        user__last_name="Learner",
        user__email="alice@example.com",
        user__username="uniquelearner",
        rating="4.5",
        comment="Excellent explanations",
        response="Thanks for reviewing",
        created_at=datetime(2026, 1, 15, 12, tzinfo=timezone.utc),
    )
    other = RatingFactory(
        course__instructor=instructor,
        rating="2.0",
        comment="Needs improvement",
        response=None,
        created_at=datetime(2026, 1, 17, 12, tzinfo=timezone.utc),
    )
    deleted = RatingFactory(course=matched.course, user=matched.user, rating="4.5")
    deleted.soft_delete()
    foreign = RatingFactory(rating="4.5")
    client.force_authenticate(instructor)
    return reverse(request.param), matched, other, foreign


@pytest.mark.parametrize(
    "query",
    [
        {"rating": "4.5"},
        {"rating_min": "4.5", "rating_max": "4.5"},
        {"created_at_after": "2026-01-15", "created_at_before": "2026-01-15"},
        {"search": "Unique Python"},
        {"search": "EXCELLENT"},
        {"search": "reviewing"},
        {"search": "Alice Learner"},
        {"search": "alice@example.com"},
        {"search": "uniquelearner"},
        {
            "search": "explanations",
            "rating_min": "4",
            "created_at_before": "2026-01-16",
        },
    ],
)
def test_filters_and_search(client, ratings, query):
    url, matched, _, _ = ratings
    response = client.get(url, query)
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(matched.pk)]


@pytest.mark.parametrize("field", ["course", "user"])
def test_related_filters_and_scope(client, ratings, field):
    url, matched, _, foreign = ratings
    response = client.get(url, {field: str(getattr(matched, f"{field}_id"))})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(matched.pk)]
    response = client.get(url, {field: str(getattr(foreign, f"{field}_id"))})
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.parametrize(
    "query",
    [
        {"rating_min": "4.6"},
        {"rating_max": "1.9"},
        {"created_at_after": "2026-01-18"},
        {"created_at_before": "2026-01-14"},
        {"search": "no-match-xyz"},
    ],
)
def test_empty_results(client, ratings, query):
    url, _, _, _ = ratings
    response = client.get(url, query)
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.parametrize(
    "field",
    [
        "course",
        "user",
        "rating",
        "rating_min",
        "rating_max",
        "created_at_after",
        "created_at_before",
    ],
)
def test_invalid_filters(client, ratings, field):
    url, _, _, _ = ratings
    response = client.get(url, {field: "invalid"})
    assert response.status_code == 400
    assert field in response.data


@pytest.mark.parametrize("ordering", ["created_at", "-created_at", "rating", "-rating"])
def test_ordering(client, ratings, ordering):
    url, matched, other, _ = ratings
    expected = (
        [matched, other] if ordering in ("created_at", "-rating") else [other, matched]
    )
    response = client.get(url, {"ordering": ordering})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [
        str(row.pk) for row in expected
    ]
