import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode

from apps.core.services import send_email

logger = logging.getLogger(__name__)


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.id) + str(timestamp) + str(user.status)


class PasswordResetToken(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.id) + str(timestamp) + str(user.password_changed_at)


account_activation_token = AccountActivationTokenGenerator()
password_reset_token = PasswordResetToken()


def generate_uid(user):
    """
    Generates UID for a given user.
    """
    uid = urlsafe_base64_encode(force_bytes(user.id))
    return uid


def send_email_with_context(subject, template, user, context):
    """Generalized function to send an email with context."""
    try:
        email_html_message = render_to_string(template, context)
    except Exception as exc:
        logger.error(
            "Failed to render mail template '%s': %s", template, exc, exc_info=True
        )
        return

    email_data = {
        "subject": subject,
        "body": strip_tags(email_html_message),
        "to_email": user.email,
        "html_body": email_html_message,
    }

    try:
        send_email.delay(email_data)
    except Exception as exc:
        logger.error("Failed to enqueue send_email task: %s", exc, exc_info=True)


def send_verify_email(user):
    uid = generate_uid(user)
    token = account_activation_token.make_token(user)

    frontend_base = settings.FRONTEND_URL.rstrip("/")
    context = {
        "username": user.username,
        "link": f"{frontend_base}/activate-account/{uid}/{token}/",
    }

    # Send verification email
    send_email_with_context(
        "Verify your email", "user/verify_email.html", user, context
    )


def send_reset_password_email(user):
    uid = generate_uid(user)
    token = password_reset_token.make_token(user)

    frontend_base = settings.FRONTEND_URL.rstrip("/")
    context = {
        "username": user.username,
        "link": f"{frontend_base}/reset-password/{uid}/{token}/",
    }

    # Send reset password email
    send_email_with_context(
        "Reset your password", "user/reset_password.html", user, context
    )
