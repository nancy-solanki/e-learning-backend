from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, Group

from apps.users.tests.factories import UserFactory
from apps.wallet.tests.factories import WalletFactory
from apps.wallet.views import IsInstructorOrAdmin

pytestmark = pytest.mark.django_db
BASE = "/api/v1/wallet/"


def test_anonymous_and_student_denied(client):
    assert client.get(BASE).status_code == 401
    client.force_authenticate(UserFactory())
    assert client.get(BASE).status_code == 403
    assert not IsInstructorOrAdmin().has_permission(
        SimpleNamespace(user=AnonymousUser()), None
    )


@pytest.mark.parametrize("role", ["instructor", "admin"])
def test_owner_can_read_wallet(client, wallet, role):
    wallet.user.groups.add(Group.objects.get_or_create(name=role)[0])
    client.force_authenticate(wallet.user)
    assert client.get(BASE).data["id"] == str(wallet.pk)
    assert client.get(BASE + f"{wallet.pk}/").status_code == 200
    foreign = WalletFactory()
    assert client.get(BASE + f"{foreign.pk}/").status_code == 404


def test_missing_and_deleted_wallet(client, wallet):
    wallet.user.become_instructor()
    client.force_authenticate(wallet.user)
    wallet.soft_delete()
    response = client.get(BASE)
    assert response.status_code == 404
    assert response.data == {"detail": "Wallet not found."}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_readonly(client, wallet, method):
    wallet.user.become_instructor()
    client.force_authenticate(wallet.user)
    target = BASE if method == "post" else BASE + f"{wallet.pk}/"
    assert getattr(client, method)(target).status_code == 405


@pytest.mark.parametrize(
    "field", ["current_earnings", "total_earnings", "total_withdraws"]
)
@pytest.mark.parametrize(
    "suffix,value,expected",
    [
        ("", "100", 200),
        ("", "99", 404),
        ("_min", "100", 200),
        ("_min", "101", 404),
        ("_max", "100", 200),
        ("_max", "99", 404),
        ("_min", "invalid", 400),
    ],
)
def test_amount_filters(client, wallet, field, suffix, value, expected):
    wallet.user.become_instructor()
    client.force_authenticate(wallet.user)
    setattr(wallet, field, 100)
    wallet.save()
    response = client.get(BASE, {field + suffix: value})
    assert response.status_code == expected
    if expected == 200:
        assert response.data["id"] == str(wallet.pk)


@pytest.mark.parametrize("field", ["username", "first_name", "last_name", "email"])
def test_search_owner_details(client, wallet, field):
    wallet.user.become_instructor()
    setattr(
        wallet.user,
        field,
        "WalletSearch@example.com" if field == "email" else "WalletSearch",
    )
    wallet.user.save()
    client.force_authenticate(wallet.user)
    assert client.get(BASE, {"search": "walletsearch"}).data["id"] == str(wallet.pk)
    assert client.get(BASE, {"search": "does-not-match"}).status_code == 404


def test_search_id_and_combined_filters(client, wallet):
    wallet.user.become_instructor()
    client.force_authenticate(wallet.user)
    query = {
        "search": str(wallet.pk),
        "is_site_wallet": "false",
        "current_earnings_max": 0,
    }
    assert client.get(BASE, query).data["id"] == str(wallet.pk)
    query["is_site_wallet"] = "true"
    assert client.get(BASE, query).status_code == 404


@pytest.mark.parametrize(
    "query,expected",
    [
        ({"created_at_after": "2026-01-15", "created_at_before": "2026-01-15"}, 200),
        ({"created_at_after": "2026-01-16"}, 404),
        ({"created_at_before": "2026-01-14"}, 404),
        ({"created_at_after": "invalid"}, 400),
    ],
)
def test_creation_date_filters(client, wallet, query, expected):
    from datetime import datetime, timezone

    wallet.user.become_instructor()
    client.force_authenticate(wallet.user)
    wallet.created_at = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    wallet.save()
    assert client.get(BASE, query).status_code == expected


@pytest.mark.parametrize("role", ["instructor", "admin"])
def test_search_cannot_expose_foreign_or_deleted_wallets(client, wallet, role):
    wallet.user.groups.add(Group.objects.get_or_create(name=role)[0])
    client.force_authenticate(wallet.user)
    foreign = WalletFactory(current_earnings=123)
    deleted = WalletFactory(user=wallet.user, current_earnings=123)
    deleted.soft_delete()
    for hidden in [foreign, deleted]:
        query = {"search": str(hidden.pk), "current_earnings": 123}
        assert client.get(BASE, query).status_code == 404
        assert client.get(BASE + f"{hidden.pk}/", query).status_code == 404
