"""
Integration-style view tests for apps.auth endpoints.

Each request hits the real URL router and the real serializer/service stack;
only external side-effects (Celery tasks, email) are mocked.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth.services import account_activation_token, password_reset_token
from apps.users.tests.factories import UserFactory

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def active_user(db):
    user = UserFactory(status=User.Status.ACTIVE)
    # factory skip_postgeneration_save=True means set_password() is applied
    # in-memory but not flushed back to DB — force a save here so that
    # TokenObtainPairView can authenticate with the hashed password.
    user.save()
    return user


@pytest.fixture
def pending_user(db):
    return UserFactory(status=User.Status.PENDING)


@pytest.fixture
def auth_client(api_client, active_user):
    api_client.force_authenticate(user=active_user)
    return api_client


def _uid(user):
    return urlsafe_base64_encode(force_bytes(user.id))


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/sign-up/
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserRegistrationView:
    url = "/api/v1/auth/sign-up/"

    valid_payload = {
        "email": "signup@example.com",
        "username": "signupuser",
        "first_name": "Sign",
        "last_name": "Up",
        "password": "StrongPass1!",
    }

    def test_valid_registration_returns_201(self, api_client, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        response = api_client.post(self.url, self.valid_payload)
        assert response.status_code == status.HTTP_201_CREATED

    def test_response_contains_message(self, api_client, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        response = api_client.post(self.url, self.valid_payload)
        assert "message" in response.data

    def test_user_is_created_in_db(self, api_client, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        api_client.post(self.url, self.valid_payload)
        assert User.objects.filter(email=self.valid_payload["email"]).exists()

    def test_duplicate_email_returns_400(self, api_client, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        UserFactory(email=self.valid_payload["email"])
        payload = {**self.valid_payload, "username": "anotheruser"}
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email_returns_400(self, api_client):
        payload = {**self.valid_payload}
        del payload["email"]
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_username_returns_400(self, api_client):
        payload = {**self.valid_payload, "email": "other@example.com"}
        del payload["username"]
        response = api_client.post(self.url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_method_not_allowed(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/sign-in/   (simplejwt TokenObtainPairView)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSignInView:
    url = "/api/v1/auth/sign-in/"

    def test_valid_credentials_return_200(self, api_client, active_user):
        response = api_client.post(
            self.url, {"email": active_user.email, "password": "testpassword123!"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_response_contains_access_and_refresh(self, api_client, active_user):
        response = api_client.post(
            self.url, {"email": active_user.email, "password": "testpassword123!"}
        )
        assert "access" in response.data
        assert "refresh" in response.data

    def test_wrong_password_returns_401(self, api_client, active_user):
        response = api_client.post(
            self.url, {"email": active_user.email, "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_email_returns_401(self, api_client):
        response = api_client.post(
            self.url, {"email": "ghost@example.com", "password": "pass"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_password_returns_400(self, api_client, active_user):
        response = api_client.post(self.url, {"email": active_user.email})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email_returns_400(self, api_client):
        response = api_client.post(self.url, {"password": "testpassword123!"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/sign-out/
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserLogoutView:
    url = "/api/v1/auth/sign-out/"

    def test_authenticated_logout_returns_204(self, auth_client, active_user):
        refresh = str(RefreshToken.for_user(active_user))
        response = auth_client.post(self.url, {"refresh_token": refresh})
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_unauthenticated_returns_401(self, api_client, active_user):
        refresh = str(RefreshToken.for_user(active_user))
        response = api_client.post(self.url, {"refresh_token": refresh})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_returns_400(self, auth_client):
        response = auth_client.post(self.url, {"refresh_token": "bad.token.value"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_token_field_returns_400(self, auth_client):
        response = auth_client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_reuse_blacklisted_token_returns_400(self, auth_client, active_user):
        refresh = str(RefreshToken.for_user(active_user))
        auth_client.post(self.url, {"refresh_token": refresh})
        response = auth_client.post(self.url, {"refresh_token": refresh})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/refresh/
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestTokenRefreshView:
    url = "/api/v1/auth/refresh/"

    def test_valid_refresh_returns_200(self, api_client, active_user):
        refresh = str(RefreshToken.for_user(active_user))
        response = api_client.post(self.url, {"refresh": refresh})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_invalid_refresh_returns_401(self, api_client):
        response = api_client.post(self.url, {"refresh": "not-a-token"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_refresh_returns_400(self, api_client):
        response = api_client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/change-password/
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserChangePasswordView:
    url = "/api/v1/auth/change-password/"

    def test_correct_old_password_returns_200(self, auth_client):
        response = auth_client.post(
            self.url,
            {"old_password": "testpassword123!", "new_password": "NewStrongPass9!"},
        )
        assert response.status_code == status.HTTP_200_OK

    def test_response_contains_message(self, auth_client):
        response = auth_client.post(
            self.url,
            {"old_password": "testpassword123!", "new_password": "NewStrongPass9!"},
        )
        assert "message" in response.data

    def test_wrong_old_password_returns_400(self, auth_client):
        response = auth_client.post(
            self.url,
            {"old_password": "wrongpassword", "new_password": "NewStrongPass9!"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.post(
            self.url,
            {"old_password": "testpassword123!", "new_password": "NewStrongPass9!"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_old_password_returns_400(self, auth_client):
        response = auth_client.post(self.url, {"new_password": "NewStrongPass9!"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_new_password_returns_400(self, auth_client):
        response = auth_client.post(self.url, {"old_password": "testpassword123!"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_new_password_is_persisted(self, auth_client, active_user):
        auth_client.post(
            self.url,
            {"old_password": "testpassword123!", "new_password": "NewStrongPass9!"},
        )
        active_user.refresh_from_db()
        assert active_user.check_password("NewStrongPass9!")


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/send-reset-password-email/
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSendPasswordResetEmailView:
    url = "/api/v1/auth/send-reset-password-email/"

    def test_valid_active_email_returns_200(self, api_client, mocker, active_user):
        mocker.patch("apps.auth.serializers.send_reset_password_email")
        response = api_client.post(self.url, {"email": active_user.email})
        assert response.status_code == status.HTTP_200_OK

    def test_nonexistent_email_returns_400(self, api_client):
        response = api_client.post(self.url, {"email": "nobody@example.com"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email_returns_400(self, api_client):
        response = api_client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_email_format_returns_400(self, api_client):
        response = api_client.post(self.url, {"email": "not-an-email"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_not_allowed(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_reset_email_is_sent_for_active_user(self, api_client, mocker, active_user):
        mock_send = mocker.patch("apps.auth.serializers.send_reset_password_email")
        api_client.post(self.url, {"email": active_user.email})
        mock_send.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/reset-password/<uid>/<token>/
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserPasswordResetView:
    base_url = "/api/v1/auth/reset-password/"

    def _url(self, user):
        uid = _uid(user)
        token = password_reset_token.make_token(user)
        return f"{self.base_url}{uid}/{token}/", uid, token

    def test_valid_reset_returns_200(self, api_client, active_user):
        url, _, _ = self._url(active_user)
        response = api_client.post(url, {"password": "FreshPass99!"})
        assert response.status_code == status.HTTP_200_OK

    def test_password_is_updated(self, api_client, active_user):
        url, _, _ = self._url(active_user)
        api_client.post(url, {"password": "FreshPass99!"})
        active_user.refresh_from_db()
        assert active_user.check_password("FreshPass99!")

    def test_invalid_token_returns_400(self, api_client, active_user):
        uid = _uid(active_user)
        url = f"{self.base_url}{uid}/bad-token/"
        response = api_client.post(url, {"password": "FreshPass99!"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_password_returns_400(self, api_client, active_user):
        url, _, _ = self._url(active_user)
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_cannot_be_reused(self, api_client, active_user):
        url, _, _ = self._url(active_user)
        api_client.post(url, {"password": "FreshPass99!"})
        # After password_changed_at is set, old token is invalid
        response = api_client.post(url, {"password": "AnotherPass99!"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/auth/activate-account/<uid>/<token>/
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserActivateAccountView:
    base_url = "/api/v1/auth/activate-account/"

    def _url(self, user):
        uid = _uid(user)
        token = account_activation_token.make_token(user)
        return f"{self.base_url}{uid}/{token}/"

    def test_valid_token_returns_200(self, api_client, pending_user):
        url = self._url(pending_user)
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK

    def test_account_status_set_to_active(self, api_client, pending_user):
        url = self._url(pending_user)
        api_client.post(url)
        pending_user.refresh_from_db()
        assert pending_user.status == User.Status.ACTIVE

    def test_invalid_token_returns_400(self, api_client, pending_user):
        uid = _uid(pending_user)
        url = f"{self.base_url}{uid}/invalid-token/"
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_uid_returns_400(self, api_client):
        url = f"{self.base_url}baduid/sometoken/"
        response = api_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_cannot_be_reused_after_activation(self, api_client, pending_user):
        url = self._url(pending_user)
        api_client.post(url)  # first activation
        response = api_client.post(url)  # second attempt with same token
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_not_allowed(self, api_client, pending_user):
        url = self._url(pending_user)
        response = api_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
