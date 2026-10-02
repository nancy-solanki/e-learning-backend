import re
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from apps.auth.services import account_activation_token, generate_uid
from apps.users.invitations import invitation_token

User = get_user_model()
pytestmark = pytest.mark.django_db
PAYLOAD = {
    "email": "Invited@example.com",
    "username": "Invited",
    "first_name": "New",
    "last_name": "Learner",
}
PASSWORD = "Strong-Invitation-Passphrase-729!"


def invite(client, **overrides):
    response = client.post(
        reverse("user:invite"), {**PAYLOAD, **overrides}, format="json"
    )
    assert response.status_code == 201, response.data
    return User.objects.get(pk=response.data["id"])


def accept_url(user, token=None):
    return reverse(
        "auth:accept-invite",
        kwargs={
            "uid": generate_uid(user),
            "token": token or invitation_token.make_token(user),
        },
    )


def test_invite_email_and_activation(admin_client, api_client):
    user = invite(admin_client)
    assert user.email == "invited@example.com"
    assert user.username == "invited"
    assert not user.is_active and not user.has_usable_password()
    assert user.status == User.Status.PENDING
    assert list(user.groups.values_list("name", flat=True)) == ["student"]
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    match = re.search(
        r"https://example.com/accept-invite/([^/]+)/([^/]+)/", mail.outbox[0].body
    )
    assert match
    url = reverse("auth:accept-invite", kwargs={"uid": match[1], "token": match[2]})
    assert api_client.get(url).status_code == 405
    assert (
        api_client.post(
            "/api/v1/auth/sign-in/", {"email": user.email, "password": PASSWORD}
        ).status_code
        == 401
    )
    response = api_client.post(url, {"password": PASSWORD}, format="json")
    assert response.status_code == 200, response.data
    user.refresh_from_db()
    assert user.is_active and user.status == User.Status.ACTIVE
    assert user.check_password(PASSWORD)
    assert user.password_changed_at
    assert api_client.post(url, {"password": PASSWORD}).status_code == 400
    assert (
        api_client.post(
            "/api/v1/auth/sign-in/", {"email": user.email, "password": PASSWORD}
        ).status_code
        == 200
    )


@pytest.mark.parametrize("authenticated,expected", [(False, 401), (True, 403)])
def test_invite_requires_admin(api_client, user, authenticated, expected):
    if authenticated:
        api_client.force_authenticate(user)
    assert api_client.post(reverse("user:invite"), PAYLOAD).status_code == expected
    assert (
        api_client.post(
            reverse("user:resend-invite", kwargs={"pk": user.pk})
        ).status_code
        == expected
    )


def test_admin_group_can_invite(api_client, user):
    user.groups.add(Group.objects.get_or_create(name="admin")[0])
    api_client.force_authenticate(user)
    invited = invite(api_client, role="instructor")
    assert invited.groups.filter(name="instructor").exists()
    assert not invited.is_staff and not invited.is_superuser


@pytest.mark.parametrize(
    "extra",
    [
        {"password": PASSWORD},
        {"is_superuser": True},
        {"status": "AC"},
        {"role": "superuser"},
    ],
)
def test_reject_unaccepted_fields(admin_client, extra):
    response = admin_client.post(
        reverse("user:invite"), {**PAYLOAD, **extra}, format="json"
    )
    assert response.status_code == 400
    assert not User.objects.filter(email__iexact=PAYLOAD["email"]).exists()


@pytest.mark.parametrize("field", ["email", "username"])
def test_case_insensitive_duplicate(admin_client, field):
    invite(admin_client)
    data = {**PAYLOAD, "email": "other@example.com", "username": "other"}
    data[field] = PAYLOAD[field].upper()
    assert admin_client.post(reverse("user:invite"), data).status_code == 400
    assert len(mail.outbox) == 1


def test_invitation_is_queued_without_sending_in_request(admin_client):
    with patch("apps.users.invitations.send_email.delay") as enqueue:
        user = invite(admin_client)
    enqueue.assert_called_once()
    assert enqueue.call_args.args[0]["to_email"] == user.email
    assert "/accept-invite/" in enqueue.call_args.args[0]["html_body"]
    assert len(mail.outbox) == 0


def test_queue_failure_rolls_back_creation(admin_client):
    with patch(
        "apps.users.invitations.send_email.delay",
        side_effect=RuntimeError("broker down"),
    ):
        response = admin_client.post(reverse("user:invite"), PAYLOAD)
    assert response.status_code == 503
    assert not User.objects.filter(email__iexact=PAYLOAD["email"]).exists()


def test_resend_rotates_token_and_queue_failure_preserves_old_link(
    admin_client, api_client
):
    user = invite(admin_client)
    old_url = accept_url(user)
    resend = reverse("user:resend-invite", kwargs={"pk": user.pk})
    with patch(
        "apps.users.invitations.send_email.delay",
        side_effect=RuntimeError("broker down"),
    ):
        assert admin_client.post(resend).status_code == 503
    user.refresh_from_db()
    assert accept_url(user) == old_url
    assert admin_client.post(resend).status_code == 200
    user.refresh_from_db()
    assert len(mail.outbox) == 2
    assert api_client.post(old_url, {"password": PASSWORD}).status_code == 400
    assert api_client.post(accept_url(user), {"password": PASSWORD}).status_code == 200
    assert admin_client.post(resend).status_code == 400


@pytest.mark.parametrize("password", ["", "123", "password", "123456789", "invited"])
def test_weak_password_keeps_invitation_pending(admin_client, api_client, password):
    user = invite(admin_client)
    response = api_client.post(accept_url(user), {"password": password})
    assert response.status_code == 400
    assert "password" in response.data
    user.refresh_from_db()
    assert not user.is_active and not user.has_usable_password()


@pytest.mark.parametrize(
    "reason", ["expired", "tampered", "wrong-purpose", "deleted", "suspended"]
)
def test_invalid_invitation(admin_client, api_client, settings, reason):
    user = invite(admin_client)
    token = invitation_token.make_token(user)
    if reason == "expired":
        settings.PASSWORD_RESET_TIMEOUT = 1
        with patch.object(
            invitation_token,
            "_now",
            return_value=invitation_token._now() - timedelta(seconds=5),
        ):
            token = invitation_token.make_token(user)
    elif reason == "tampered":
        token += "bad"
    elif reason == "wrong-purpose":
        token = account_activation_token.make_token(user)
    elif reason == "deleted":
        user.deleted_at = timezone.now()
        user.save()
    elif reason == "suspended":
        user.status = User.Status.SUSPEND
        user.save()
    assert (
        api_client.post(accept_url(user, token), {"password": PASSWORD}).status_code
        == 400
    )
    user.refresh_from_db()
    assert not user.is_active and not user.has_usable_password()


@pytest.mark.parametrize(
    "uid",
    ["bad", "!", "bm90LWEtdXVpZA", "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMDAx"],
)
def test_invalid_uid(api_client, uid):
    url = reverse("auth:accept-invite", kwargs={"uid": uid, "token": "bad-token"})
    assert api_client.post(url, {"password": PASSWORD}).status_code == 400
