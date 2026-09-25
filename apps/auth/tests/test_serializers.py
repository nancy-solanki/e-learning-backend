"""
Unit tests for apps.auth.serializers.

Strategy
--------
* Heavy use of ``pytest-mock`` (``mocker`` fixture) to patch email / Celery
  tasks so tests stay fast and require no SMTP / Redis.
* DB is touched only where the serializer itself writes to it.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth.serializers import (
    SendPasswordResetEmailSerializer,
    SocialLoginSerializer,
    UserActivateAccountSerializer,
    UserChangePasswordSerializer,
    UserLogoutSerializer,
    UserPasswordResetSerializer,
    UserRegistrationSerializer,
)
from apps.auth.services import account_activation_token, password_reset_token
from apps.users.tests.factories import UserFactory

User = get_user_model()

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _uid(user):
    return urlsafe_base64_encode(force_bytes(user.id))


# ─────────────────────────────────────────────────────────────────────────────
# UserRegistrationSerializer
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserRegistrationSerializer:
    """Registration serializer: validation, user creation, group assignment."""

    valid_payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "first_name": "New",
        "last_name": "User",
        "password": "StrongPass1!",
    }

    def test_valid_data_is_valid(self, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        s = UserRegistrationSerializer(data=self.valid_payload)
        assert s.is_valid(), s.errors

    def test_creates_user_in_db(self, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        s = UserRegistrationSerializer(data=self.valid_payload)
        s.is_valid(raise_exception=True)
        user = s.save()
        assert User.objects.filter(pk=user.pk).exists()

    def test_password_is_hashed(self, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        s = UserRegistrationSerializer(data=self.valid_payload)
        s.is_valid(raise_exception=True)
        user = s.save()
        assert user.check_password(self.valid_payload["password"])

    def test_user_assigned_to_student_group(self, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        s = UserRegistrationSerializer(data=self.valid_payload)
        s.is_valid(raise_exception=True)
        user = s.save()
        assert user.groups.filter(name="student").exists()

    def test_verify_email_called(self, mocker):
        mock_send = mocker.patch("apps.auth.serializers.send_verify_email")
        s = UserRegistrationSerializer(data=self.valid_payload)
        s.is_valid(raise_exception=True)
        s.save()
        mock_send.assert_called_once()

    def test_email_send_failure_does_not_block_registration(self, mocker):
        mocker.patch(
            "apps.auth.serializers.send_verify_email",
            side_effect=Exception("SMTP down"),
        )
        s = UserRegistrationSerializer(data=self.valid_payload)
        s.is_valid(raise_exception=True)
        user = s.save()  # must not raise
        assert user.pk is not None

    def test_missing_email_is_invalid(self):
        payload = {**self.valid_payload}
        del payload["email"]
        s = UserRegistrationSerializer(data=payload)
        assert not s.is_valid()
        assert "email" in s.errors

    def test_missing_username_is_invalid(self):
        payload = {**self.valid_payload, "email": "other@example.com"}
        del payload["username"]
        s = UserRegistrationSerializer(data=payload)
        assert not s.is_valid()
        assert "username" in s.errors

    def test_duplicate_email_is_invalid(self, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        UserFactory(email="dup@example.com")
        payload = {
            **self.valid_payload,
            "email": "dup@example.com",
            "username": "dupuser",
        }
        s = UserRegistrationSerializer(data=payload)
        assert not s.is_valid()
        assert "email" in s.errors

    def test_password_not_returned_in_representation(self, mocker):
        mocker.patch("apps.auth.serializers.send_verify_email")
        s = UserRegistrationSerializer(data=self.valid_payload)
        s.is_valid(raise_exception=True)
        # password is write_only — not in serializer's data
        assert "password" not in s.data


@pytest.mark.django_db
class TestSocialLoginSerializer:
    def test_social_user_gets_active_student_account(self, mocker):
        user = UserFactory(status=User.Status.PENDING)
        serializer = SocialLoginSerializer()
        mocker.patch(
            "dj_rest_auth.registration.serializers.SocialLoginSerializer.validate",
            return_value={"user": user},
        )

        serializer.validate({})

        user.refresh_from_db()
        assert user.status == User.Status.ACTIVE
        assert user.groups.filter(name="student").exists()


# ─────────────────────────────────────────────────────────────────────────────
# UserActivateAccountSerializer
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserActivateAccountSerializer:
    """Account activation via uid + token."""

    def _make_pending_user(self):
        return UserFactory(status=User.Status.PENDING)

    def test_valid_token_activates_user(self):
        user = self._make_pending_user()
        uid = _uid(user)
        token = account_activation_token.make_token(user)
        s = UserActivateAccountSerializer(data={}, context={"uid": uid, "token": token})
        assert s.is_valid(), s.errors
        user.refresh_from_db()
        assert user.status == User.Status.ACTIVE

    def test_invalid_token_raises_validation_error(self):
        user = self._make_pending_user()
        uid = _uid(user)
        s = UserActivateAccountSerializer(
            data={}, context={"uid": uid, "token": "bad-token"}
        )
        assert not s.is_valid()
        assert "non_field_errors" in s.errors or s.errors  # any validation error

    def test_invalid_uid_raises_validation_error(self):
        s = UserActivateAccountSerializer(
            data={}, context={"uid": "notbase64!!", "token": "anything"}
        )
        assert not s.is_valid()

    def test_missing_user_uid_raises_validation_error(self):
        uid = urlsafe_base64_encode(force_bytes(999999999))
        s = UserActivateAccountSerializer(
            data={}, context={"uid": uid, "token": "anything"}
        )
        assert not s.is_valid()

    def test_already_active_user_token_is_invalid(self):
        """After activation the token's hash value changes → token no longer valid."""
        user = self._make_pending_user()
        uid = _uid(user)
        token = account_activation_token.make_token(user)
        # first activation
        s1 = UserActivateAccountSerializer(
            data={}, context={"uid": uid, "token": token}
        )
        s1.is_valid()
        # second attempt with same token
        s2 = UserActivateAccountSerializer(
            data={}, context={"uid": uid, "token": token}
        )
        assert not s2.is_valid()


# ─────────────────────────────────────────────────────────────────────────────
# UserLogoutSerializer
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserLogoutSerializer:
    """Token blacklisting on logout."""

    def test_valid_refresh_token_is_accepted(self):
        user = UserFactory()
        refresh = str(RefreshToken.for_user(user))
        s = UserLogoutSerializer(data={"refresh_token": refresh})
        assert s.is_valid(), s.errors

    def test_save_blacklists_token(self):
        user = UserFactory()
        refresh = RefreshToken.for_user(user)
        s = UserLogoutSerializer(data={"refresh_token": str(refresh)})
        s.is_valid(raise_exception=True)
        s.save()
        # Using the same token again should raise a validation error
        s2 = UserLogoutSerializer(data={"refresh_token": str(refresh)})
        s2.is_valid(raise_exception=True)
        with pytest.raises(Exception):
            s2.save()

    def test_invalid_token_raises_validation_error(self):
        s = UserLogoutSerializer(data={"refresh_token": "not.a.valid.token"})
        s.is_valid(raise_exception=True)
        with pytest.raises(Exception):
            s.save()

    def test_missing_refresh_token_field_is_invalid(self):
        s = UserLogoutSerializer(data={})
        assert not s.is_valid()
        assert "refresh_token" in s.errors


# ─────────────────────────────────────────────────────────────────────────────
# UserChangePasswordSerializer
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserChangePasswordSerializer:
    """Password change: old password verification and new password persistence."""

    RAW_PASSWORD = "testpassword123!"

    def test_correct_old_password_is_valid(self):
        user = UserFactory()
        s = UserChangePasswordSerializer(
            data={"old_password": self.RAW_PASSWORD, "new_password": "NewPass99!"},
            context={"user": user},
        )
        assert s.is_valid(), s.errors

    def test_wrong_old_password_is_invalid(self):
        user = UserFactory()
        s = UserChangePasswordSerializer(
            data={"old_password": "wrongpassword", "new_password": "NewPass99!"},
            context={"user": user},
        )
        assert not s.is_valid()

    def test_new_password_is_saved(self):
        user = UserFactory()
        s = UserChangePasswordSerializer(
            data={"old_password": self.RAW_PASSWORD, "new_password": "NewPass99!"},
            context={"user": user},
        )
        s.is_valid(raise_exception=True)
        user.refresh_from_db()
        assert user.check_password("NewPass99!")

    def test_password_changed_at_is_set(self):
        user = UserFactory()
        assert user.password_changed_at is None
        s = UserChangePasswordSerializer(
            data={"old_password": self.RAW_PASSWORD, "new_password": "NewPass99!"},
            context={"user": user},
        )
        s.is_valid(raise_exception=True)
        user.refresh_from_db()
        assert user.password_changed_at is not None

    def test_missing_old_password_is_invalid(self):
        user = UserFactory()
        s = UserChangePasswordSerializer(
            data={"new_password": "NewPass99!"}, context={"user": user}
        )
        assert not s.is_valid()

    def test_missing_new_password_is_invalid(self):
        user = UserFactory()
        s = UserChangePasswordSerializer(
            data={"old_password": self.RAW_PASSWORD}, context={"user": user}
        )
        assert not s.is_valid()


# ─────────────────────────────────────────────────────────────────────────────
# SendPasswordResetEmailSerializer
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSendPasswordResetEmailSerializer:
    """Password reset email dispatch: happy path & guard clauses."""

    def test_valid_email_is_valid(self, mocker):
        mocker.patch("apps.auth.serializers.send_reset_password_email")
        user = UserFactory(status=User.Status.ACTIVE)
        s = SendPasswordResetEmailSerializer(data={"email": user.email})
        assert s.is_valid(), s.errors

    def test_send_reset_email_called_for_active_user(self, mocker):
        mock_send = mocker.patch("apps.auth.serializers.send_reset_password_email")
        user = UserFactory(status=User.Status.ACTIVE)
        s = SendPasswordResetEmailSerializer(data={"email": user.email})
        s.is_valid(raise_exception=True)
        mock_send.assert_called_once_with(user)

    def test_nonexistent_email_raises_validation_error(self):
        s = SendPasswordResetEmailSerializer(data={"email": "ghost@example.com"})
        assert not s.is_valid()

    def test_missing_email_field_is_invalid(self):
        s = SendPasswordResetEmailSerializer(data={})
        assert not s.is_valid()
        assert "email" in s.errors

    def test_invalid_email_format_is_invalid(self):
        s = SendPasswordResetEmailSerializer(data={"email": "not-an-email"})
        assert not s.is_valid()
        assert "email" in s.errors

    def test_pending_user_does_not_get_reset_email(self, mocker):
        """PENDING users should not receive a password reset link."""
        mock_send = mocker.patch("apps.auth.serializers.send_reset_password_email")
        user = UserFactory(status=User.Status.PENDING)
        s = SendPasswordResetEmailSerializer(data={"email": user.email})
        assert not s.is_valid()
        assert "Email is not verified" in str(s.errors)
        mock_send.assert_not_called()

    def test_suspended_user_does_not_get_reset_email(self, mocker):
        mock_send = mocker.patch("apps.auth.serializers.send_reset_password_email")
        user = UserFactory(status=User.Status.SUSPEND)
        s = SendPasswordResetEmailSerializer(data={"email": user.email})
        assert not s.is_valid()
        assert "Account is not active" in str(s.errors)
        mock_send.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# UserPasswordResetSerializer
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserPasswordResetSerializer:
    """Password reset via uid + token."""

    def test_valid_token_resets_password(self):
        user = UserFactory()
        uid = _uid(user)
        token = password_reset_token.make_token(user)
        s = UserPasswordResetSerializer(
            data={"password": "BrandNewPass1!"},
            context={"uid": uid, "token": token},
        )
        assert s.is_valid(), s.errors
        user.refresh_from_db()
        assert user.check_password("BrandNewPass1!")

    def test_invalid_token_raises_validation_error(self):
        user = UserFactory()
        uid = _uid(user)
        s = UserPasswordResetSerializer(
            data={"password": "BrandNewPass1!"},
            context={"uid": uid, "token": "bad-token"},
        )
        assert not s.is_valid()

    def test_invalid_uid_raises_validation_error(self):
        s = UserPasswordResetSerializer(
            data={"password": "BrandNewPass1!"},
            context={"uid": "%%%invalid%%%", "token": "anything"},
        )
        assert not s.is_valid()

    def test_missing_password_is_invalid(self):
        user = UserFactory()
        uid = _uid(user)
        token = password_reset_token.make_token(user)
        s = UserPasswordResetSerializer(data={}, context={"uid": uid, "token": token})
        assert not s.is_valid()
        assert "password" in s.errors

    def test_password_changed_at_is_updated(self):
        user = UserFactory()
        assert user.password_changed_at is None
        uid = _uid(user)
        token = password_reset_token.make_token(user)
        s = UserPasswordResetSerializer(
            data={"password": "BrandNewPass1!"},
            context={"uid": uid, "token": token},
        )
        s.is_valid(raise_exception=True)
        user.refresh_from_db()
        assert user.password_changed_at is not None
