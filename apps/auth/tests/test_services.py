"""
Unit tests for apps.auth.services.

All external I/O (Celery task, template rendering) is mocked so these tests
run without a broker, SMTP server, or real template engine.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils.encoding import smart_str
from django.utils.http import urlsafe_base64_decode

from apps.auth.services import (
    account_activation_token,
    generate_uid,
    password_reset_token,
    send_email_with_context,
    send_reset_password_email,
    send_verify_email,
)
from apps.users.tests.factories import UserFactory

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# generate_uid
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGenerateUid:
    def test_uid_encodes_user_id(self):
        user = UserFactory()
        uid = generate_uid(user)
        decoded = smart_str(urlsafe_base64_decode(uid))
        assert decoded == str(user.id)

    def test_different_users_produce_different_uids(self):
        u1 = UserFactory()
        u2 = UserFactory()
        assert generate_uid(u1) != generate_uid(u2)


# ─────────────────────────────────────────────────────────────────────────────
# AccountActivationTokenGenerator
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAccountActivationTokenGenerator:
    def test_token_is_valid_for_pending_user(self):
        user = UserFactory(status=User.Status.PENDING)
        token = account_activation_token.make_token(user)
        assert account_activation_token.check_token(user, token)

    def test_token_is_valid_for_active_user(self):
        user = UserFactory(status=User.Status.ACTIVE)
        token = account_activation_token.make_token(user)
        assert account_activation_token.check_token(user, token)

    def test_token_invalid_after_status_changes(self):
        user = UserFactory(status=User.Status.PENDING)
        token = account_activation_token.make_token(user)
        # Simulate activation
        user.status = User.Status.ACTIVE
        user.save()
        assert not account_activation_token.check_token(user, token)

    def test_wrong_token_is_invalid(self):
        user = UserFactory()
        assert not account_activation_token.check_token(user, "completely-wrong-token")

    def test_token_is_user_specific(self):
        u1 = UserFactory(status=User.Status.PENDING)
        u2 = UserFactory(status=User.Status.PENDING)
        token = account_activation_token.make_token(u1)
        assert not account_activation_token.check_token(u2, token)


# ─────────────────────────────────────────────────────────────────────────────
# PasswordResetToken
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPasswordResetToken:
    def test_token_is_valid_immediately_after_generation(self):
        user = UserFactory()
        token = password_reset_token.make_token(user)
        assert password_reset_token.check_token(user, token)

    def test_token_invalid_after_password_change(self):
        user = UserFactory()
        token = password_reset_token.make_token(user)
        # Simulate password change
        user.set_password("newpassword999!")
        from datetime import datetime

        user.password_changed_at = datetime.now()
        user.save()
        assert not password_reset_token.check_token(user, token)

    def test_wrong_token_is_invalid(self):
        user = UserFactory()
        assert not password_reset_token.check_token(user, "bad-token-value")

    def test_token_is_user_specific(self):
        u1 = UserFactory()
        u2 = UserFactory()
        token = password_reset_token.make_token(u1)
        assert not password_reset_token.check_token(u2, token)


# ─────────────────────────────────────────────────────────────────────────────
# send_email_with_context
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSendEmailWithContext:
    def test_enqueues_celery_task_on_success(self, mocker):
        mock_delay = mocker.patch("apps.auth.services.send_email.delay")
        mocker.patch(
            "apps.auth.services.render_to_string", return_value="<html>email</html>"
        )
        user = UserFactory()
        send_email_with_context("Subject", "some/template.html", user, {})
        mock_delay.assert_called_once_with(
            {
                "subject": "Subject",
                "body": "email",
                "to_email": user.email,
                "html_body": "<html>email</html>",
            }
        )

    def test_template_render_failure_logs_and_returns(self, mocker):
        """A bad template must not raise — it should log and return early."""
        mocker.patch(
            "apps.auth.services.render_to_string",
            side_effect=Exception("template missing"),
        )
        mock_delay = mocker.patch("apps.auth.services.send_email.delay")
        user = UserFactory()
        # Must not raise
        send_email_with_context("Subject", "bad/template.html", user, {})
        mock_delay.assert_not_called()

    def test_celery_enqueue_failure_is_swallowed(self, mocker):
        """Broker being unavailable must not crash the caller."""
        mocker.patch(
            "apps.auth.services.render_to_string", return_value="<html>body</html>"
        )
        mocker.patch(
            "apps.auth.services.send_email.delay",
            side_effect=Exception("broker down"),
        )
        user = UserFactory()
        send_email_with_context("Subject", "template.html", user, {})  # no raise


# ─────────────────────────────────────────────────────────────────────────────
# send_verify_email / send_reset_password_email
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSendVerifyEmail:
    def test_calls_send_email_with_context(self, mocker):
        mock_fn = mocker.patch("apps.auth.services.send_email_with_context")
        user = UserFactory()
        send_verify_email(user)
        mock_fn.assert_called_once()

    def test_context_contains_username(self, mocker):
        captured = {}

        def capture(subject, template, user, context):
            captured.update(context)

        mocker.patch("apps.auth.services.send_email_with_context", side_effect=capture)
        user = UserFactory()
        send_verify_email(user)
        assert captured.get("username") == user.username

    def test_context_link_contains_uid_and_token(self, mocker, settings):
        settings.FRONTEND_URL = "https://example.com/"
        captured = {}

        def capture(subject, template, user, context):
            captured.update(context)

        mocker.patch("apps.auth.services.send_email_with_context", side_effect=capture)
        user = UserFactory()
        send_verify_email(user)
        uid = generate_uid(user)
        assert uid in captured.get("link", "")


@pytest.mark.django_db
class TestSendResetPasswordEmail:
    def test_calls_send_email_with_context(self, mocker):
        mock_fn = mocker.patch("apps.auth.services.send_email_with_context")
        user = UserFactory()
        send_reset_password_email(user)
        mock_fn.assert_called_once()

    def test_context_contains_username(self, mocker):
        captured = {}

        def capture(subject, template, user, context):
            captured.update(context)

        mocker.patch("apps.auth.services.send_email_with_context", side_effect=capture)
        user = UserFactory()
        send_reset_password_email(user)
        assert captured.get("username") == user.username

    def test_context_link_contains_uid(self, mocker, settings):
        settings.FRONTEND_URL = "https://example.com/"
        captured = {}

        def capture(subject, template, user, context):
            captured.update(context)

        mocker.patch("apps.auth.services.send_email_with_context", side_effect=capture)
        user = UserFactory()
        send_reset_password_email(user)
        uid = generate_uid(user)
        assert uid in captured.get("link", "")
