import logging

from django.db import transaction
from django.db.models import Q

from apps.core.services import send_templated_email

logger = logging.getLogger(__name__)


def queue_notification_email(
    recipient,
    *,
    subject: str,
    title: str,
    message: str,
    preference_required: bool = True,
    preference_field: str = "email_notifications",
    recipient_email: str | None = None,
    notify_in_app: bool = True,
    actor=None,
) -> bool:
    """Persist and broadcast an in-app notification, then queue its email."""
    if notify_in_app:
        from apps.users.notifications import create_notification

        create_notification(recipient, title=title, message=message, actor=actor)

    email = recipient_email or getattr(recipient, "email", "")
    if not isinstance(email, str) or not email.strip():
        return False
    if preference_required and not getattr(recipient, preference_field, False):
        return False

    context = {"title": title, "message": message}

    def enqueue():
        try:
            send_templated_email.delay(
                subject,
                email,
                "notification.html",
                context,
            )
        except Exception:
            logger.exception("Failed to enqueue notification email for %s", email)

    transaction.on_commit(enqueue)
    return True


def notify_course_learners(course, *, subject: str, title: str, message: str):
    from apps.enroll.models import Enroll
    from apps.users.models import User

    user_ids = Enroll.objects.filter(
        course=course,
        deleted_at__isnull=True,
    ).values_list("user_id", flat=True)
    learners = User.objects.filter(
        pk__in=user_ids,
        is_active=True,
        status=User.Status.ACTIVE,
        email_notifications=True,
    )
    for learner in learners.iterator(chunk_size=500):
        queue_notification_email(
            learner,
            subject=subject,
            title=title,
            message=message,
        )


def notify_moderators(*, subject: str, title: str, message: str):
    from apps.users.models import User

    moderators = User.objects.filter(
        Q(is_superuser=True) | Q(groups__name="admin"),
        is_active=True,
        status=User.Status.ACTIVE,
        email_notifications=True,
    ).distinct()
    for moderator in moderators.iterator(chunk_size=500):
        queue_notification_email(
            moderator,
            subject=subject,
            title=title,
            message=message,
        )
