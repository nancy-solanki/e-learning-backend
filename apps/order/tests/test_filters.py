from datetime import datetime, timezone

import pytest

from apps.coupon.tests.factories import CouponFactory
from apps.order.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(params=["user", "instructor"])
def orders(request, client):
    matched = OrderFactory(
        status="success",
        total_paid=150.5,
        coupon=CouponFactory(code="SAVEUNIQUE"),
        created_at=datetime(2026, 1, 15, 12, tzinfo=timezone.utc),
        user__first_name="Alice",
        user__last_name="Learner",
        user__username="uniquelearner",
        user__email="learner@example.com",
        course__title="Unique Python Course",
        course__instructor__first_name="Nancy",
        course__instructor__last_name="Teacher",
        course__instructor__username="uniqueteacher",
        course__instructor__email="teacher@example.com",
    )
    owner = getattr(matched, request.param)
    other = OrderFactory(
        **{request.param: owner},
        status="pending",
        is_free=True,
        total_paid=0,
        created_at=datetime(2026, 1, 17, 12, tzinfo=timezone.utc),
    )
    deleted = OrderFactory(**{request.param: owner}, status="success")
    deleted.soft_delete()
    foreign = OrderFactory(status="success")
    client.force_authenticate(owner)
    return f"/api/v1/order/{request.param}/", matched, other, foreign


@pytest.mark.parametrize(
    "query",
    [
        {"status": "success"},
        {"is_free": "false"},
        {"total_paid_min": "150.5", "total_paid_max": "150.5"},
        {"created_at_after": "2026-01-15", "created_at_before": "2026-01-15"},
        {"search": "saveunique"},
        {"search": "Unique Python"},
        {"status": "success", "search": "Alice Learner", "total_paid_min": "100"},
    ],
)
def test_filters(client, orders, query):
    url, matched, _, _ = orders
    response = client.get(url, query)
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(matched.pk)]


@pytest.mark.parametrize("field", ["course", "user", "instructor", "coupon"])
def test_related_filters(client, orders, field):
    url, matched, other, _ = orders
    value = getattr(matched, f"{field}_id")
    expected = [row for row in [other, matched] if getattr(row, f"{field}_id") == value]
    response = client.get(url, {field: str(value)})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [
        str(row.pk) for row in expected
    ]


@pytest.mark.parametrize(
    "search",
    [
        "ALICE Learner",
        "uniquelearner",
        "learner@example.com",
        "Nancy Teacher",
        "uniqueteacher",
        "teacher@example.com",
    ],
)
def test_search_people(client, orders, search):
    url, matched, _, _ = orders
    # Scope to the paid order so both list roles can share the same assertions.
    response = client.get(url, {"search": search, "is_free": "false"})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(matched.pk)]


def test_search_id_and_scope(client, orders):
    url, matched, _, foreign = orders
    assert client.get(url, {"search": str(matched.pk)}).data["count"] == 1
    assert client.get(url, {"search": str(foreign.pk)}).data["count"] == 0
    assert client.get(url, {"course": str(foreign.course_id)}).data["count"] == 0


@pytest.mark.parametrize(
    "query",
    [
        {"search": "no-match-xyz"},
        {"total_paid_min": "151"},
        {"total_paid_max": "-1"},
        {"created_at_after": "2026-01-18"},
        {"created_at_before": "2026-01-14"},
    ],
)
def test_empty_results(client, orders, query):
    url, _, _, _ = orders
    response = client.get(url, query)
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.parametrize(
    "field",
    [
        "status",
        "course",
        "user",
        "instructor",
        "coupon",
        "total_paid_min",
        "total_paid_max",
        "created_at_after",
        "created_at_before",
    ],
)
def test_invalid_filters(client, orders, field):
    url, _, _, _ = orders
    response = client.get(url, {field: "invalid"})
    assert response.status_code == 400
    assert field in response.data


@pytest.mark.parametrize(
    "ordering", ["created_at", "-created_at", "total_paid", "-total_paid"]
)
def test_ordering(client, orders, ordering):
    url, matched, other, _ = orders
    expected = (
        [matched, other]
        if ordering in ("created_at", "-total_paid")
        else [other, matched]
    )
    response = client.get(url, {"ordering": ordering})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [
        str(row.pk) for row in expected
    ]
