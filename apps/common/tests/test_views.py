from datetime import timedelta
from datetime import timezone as datetime_timezone

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from apps.enroll.models import Enroll
from apps.order.models import Order
from apps.users.tests.factories import SuperuserFactory, UserFactory
from apps.wallet.models import Wallet

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("dashboard_urls")]


@pytest.mark.parametrize(
    "endpoint", ["admin-dashboard", "admin-dashboard-stats", "admin-dashboard-charts"]
)
@pytest.mark.parametrize(
    "role, expected",
    [
        ("anonymous", 401),
        ("student", 403),
        ("instructor", 403),
        ("admin", 200),
        ("superuser", 200),
    ],
)
def test_permissions(client, endpoint, role, expected):
    if role != "anonymous":
        user = SuperuserFactory() if role == "superuser" else UserFactory()
        if role in ("admin", "instructor"):
            user.groups.add(Group.objects.get_or_create(name=role)[0])
        client.force_authenticate(user)
    assert client.get(reverse(endpoint)).status_code == expected


def test_empty_stats(client, admin):
    response = client.get(reverse("admin-dashboard-stats"))
    assert response.status_code == 200
    assert response.data == {
        "total_users": 1,
        "total_instructors": 0,
        "total_courses": 0,
        "total_enrollments": 0,
        "total_revenue": 0,
        "current_earnings": 0,
        "total_earnings": 0,
    }


def test_stats_exclude_deleted_and_unsuccessful_records(client, admin, course):
    group = Group.objects.get_or_create(name="instructor")[0]
    admin.groups.add(group)
    deleted_user = UserFactory(deleted_at=timezone.now())
    deleted_user.groups.add(group)
    Enroll.objects.create(user=admin, course=course)
    Enroll.objects.create(user=admin, course=course, deleted_at=timezone.now())
    for status, amount, deleted in [
        (Order.STATUS.SUCCESS, 12.34, None),
        (Order.STATUS.SUCCESS, 10, None),
        (Order.STATUS.PENDING, 100, None),
        (Order.STATUS.REJECTED, 100, None),
        (Order.STATUS.SUCCESS, 100, timezone.now()),
    ]:
        Order.objects.create(
            user=admin,
            instructor=admin,
            course=course,
            status=status,
            total_paid=amount,
            deleted_at=deleted,
        )
    response = client.get(reverse("admin-dashboard-stats"))
    assert response.data == {
        "total_users": 1,
        "total_instructors": 1,
        "total_courses": 1,
        "total_enrollments": 1,
        "total_revenue": 22.34,
        "current_earnings": 0,
        "total_earnings": 22.34,
    }
    course.soft_delete()
    assert client.get(reverse("admin-dashboard-stats")).data["total_courses"] == 0


def test_stats_select_active_site_wallet(client, admin):
    Wallet.objects.create(user=admin, current_earnings=999, total_earnings=999)
    Wallet.objects.create(is_site_wallet=True, current_earnings=10, total_earnings=25)
    Wallet.objects.create(
        is_site_wallet=True,
        current_earnings=999,
        total_earnings=999,
        deleted_at=timezone.now(),
    )
    data = client.get(reverse("admin-dashboard-stats")).data
    assert data["current_earnings"] == 10
    assert data["total_earnings"] == 25


def test_charts_group_and_filter_dates(client, admin, course, mocker):
    now = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
    mocker.patch("apps.common.views.timezone.now", return_value=now)
    # Explicit timestamps make aggregation independent of the time of test execution.
    admin.created_at = now
    admin.save()
    UserFactory(created_at=now)
    UserFactory(created_at=now - timedelta(days=31))
    UserFactory(created_at=now, deleted_at=now)
    yesterday = now - timedelta(days=1)
    for created, status, deleted in [
        (yesterday, Order.STATUS.SUCCESS, None),
        (now, Order.STATUS.SUCCESS, None),
        (now, Order.STATUS.SUCCESS, None),
        (now - timedelta(days=31), Order.STATUS.SUCCESS, None),
        (now, Order.STATUS.PENDING, None),
        (now, Order.STATUS.SUCCESS, now),
    ]:
        Order.objects.create(
            user=admin,
            instructor=admin,
            course=course,
            created_at=created,
            status=status,
            deleted_at=deleted,
        )
    response = client.get(reverse("admin-dashboard-charts"))
    assert response.status_code == 200
    assert response.data == {
        "orders": [
            {"date": timezone.localdate(yesterday).isoformat(), "count": 1},
            {"date": timezone.localdate(now).isoformat(), "count": 2},
        ],
        "users": [{"date": timezone.localdate(now).isoformat(), "count": 2}],
    }


def test_empty_charts(client, admin):
    admin.created_at = timezone.now() - timedelta(days=31)
    admin.save()
    assert client.get(reverse("admin-dashboard-charts")).data == {
        "orders": [],
        "users": [],
    }


def test_admin_dashboard_returns_zero_filled_utc_buckets(client, admin, mocker):
    as_of = timezone.datetime(2026, 11, 21, 12, 30, tzinfo=datetime_timezone.utc)
    mocker.patch("apps.common.views.timezone.now", return_value=as_of)
    response = client.get(reverse("admin-dashboard"), {"period": "daily"})

    assert response.status_code == 200
    assert response.data["as_of"] == "2026-11-21T12:30:00Z"
    assert response.data["metrics"] == {
        "total_users": 1,
        "active_learners": 0,
        "instructors": 0,
        "total_courses": 0,
        "published_courses": 0,
        "total_enrollments": 0,
        "enrollments_30d": 0,
        "gross_revenue": "0.00",
        "orders_30d": 0,
    }
    assert len(response.data["enrollment_trend"]) == 30
    assert response.data["enrollment_trend"][0] == {"date": "2026-10-23", "count": 0}
    assert response.data["enrollment_trend"][-1] == {"date": "2026-11-21", "count": 0}
    assert len(response.data["revenue_trend"]) == 30
    assert response.data["revenue_trend"][0]["amount"] == "0.00"
    assert response.data["recent_orders"] == []


@pytest.mark.parametrize(
    "period, expected_first, expected_count",
    [("monthly", "2025-12", 12), ("yearly", "2022", 5)],
)
def test_admin_dashboard_period_buckets(
    client, admin, mocker, period, expected_first, expected_count
):
    mocker.patch(
        "apps.common.views.timezone.now",
        return_value=timezone.datetime(2026, 11, 21, 12, tzinfo=datetime_timezone.utc),
    )
    response = client.get(reverse("admin-dashboard"), {"period": period})
    assert response.status_code == 200
    assert len(response.data["enrollment_trend"]) == expected_count
    assert response.data["enrollment_trend"][0]["date"] == expected_first


def test_admin_dashboard_rejects_unknown_period(client, admin):
    assert (
        client.get(reverse("admin-dashboard"), {"period": "weekly"}).status_code == 400
    )
