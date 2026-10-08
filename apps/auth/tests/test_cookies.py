import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/auth/"


def browser():
    client = APIClient(enforce_csrf_checks=True)
    token = client.get(BASE + "csrf/").data["csrfToken"]
    client.credentials(HTTP_X_CSRFTOKEN=token)
    return client


def test_cookie_session_lifecycle():
    user = UserFactory()
    user.status = user.Status.ACTIVE
    user.set_password("testpassword123!")
    user.save()
    client = browser()
    response = client.post(
        BASE + "sign-in/", {"email": user.email, "password": "testpassword123!"}
    )
    assert response.status_code == 200
    assert "access" not in response.data and "refresh" not in response.data
    for name in ("access_token", "refresh_token"):
        assert response.cookies[name]["httponly"]
        assert response.cookies[name]["samesite"] == "Lax"
    assert client.get("/api/v1/users/me/").status_code == 200
    old_refresh = client.cookies["refresh_token"].value
    client.cookies["access_token"] = "expired"
    response = client.post(BASE + "refresh/", {})
    assert response.status_code == 200
    assert client.cookies["refresh_token"].value != old_refresh
    assert client.get("/api/v1/users/me/").status_code == 200
    assert client.post(BASE + "sign-out/", {}).status_code == 204
    assert client.get("/api/v1/users/me/").status_code == 401
    client.cookies["refresh_token"] = old_refresh
    assert client.post(BASE + "refresh/", {}).status_code == 401


@pytest.mark.parametrize(
    "endpoint",
    ["sign-in/", "staff/sign-in/", "google/", "apple/", "refresh/", "sign-out/"],
)
def test_auth_posts_require_csrf(endpoint):
    assert (
        APIClient(enforce_csrf_checks=True).post(BASE + endpoint, {}).status_code == 403
    )


def test_cookie_authenticated_mutations_require_csrf():
    user = UserFactory()
    user.status = user.Status.ACTIVE
    user.save()
    client = APIClient(enforce_csrf_checks=True)
    client.cookies["access_token"] = str(RefreshToken.for_user(user).access_token)
    assert client.post(BASE + "change-password/", {}).status_code == 403


def test_untrusted_origin_rejected():
    client = browser()
    assert (
        client.post(
            BASE + "sign-in/", {}, HTTP_ORIGIN="https://evil.example"
        ).status_code
        == 403
    )


@pytest.mark.parametrize("endpoint", ["refresh/", "sign-out/"])
def test_body_tokens_are_not_used(endpoint):
    client = browser()
    response = client.post(
        BASE + endpoint, {"refresh": "body-token", "refresh_token": "body-token"}
    )
    assert response.status_code == (401 if endpoint == "refresh/" else 204)


@pytest.mark.parametrize("state", ["suspended", "password_changed"])
def test_refresh_rejects_revoked_account_session(state):
    from datetime import timedelta

    from django.utils import timezone

    user = UserFactory()
    token = RefreshToken.for_user(user)
    if state == "suspended":
        user.status = user.Status.SUSPEND
    else:
        user.password_changed_at = timezone.now() + timedelta(seconds=2)
    user.save()
    client = browser()
    client.cookies["refresh_token"] = str(token)
    assert client.post(BASE + "refresh/", {}).status_code == (
        403 if state == "suspended" else 401
    )


def test_social_login_response_sets_cookies_without_exposing_tokens():
    from apps.auth.views import CookieSocialLoginView

    view = CookieSocialLoginView()
    token = RefreshToken.for_user(UserFactory())
    view.user = UserFactory()
    view.access_token = token.access_token
    view.refresh_token = token
    view.get_serializer_context = lambda: {}
    response = view.get_response()
    assert response.status_code == 200
    assert "access" not in response.data and "refresh" not in response.data
    assert response.cookies["access_token"]["httponly"]
    assert response.cookies["refresh_token"]["httponly"]
