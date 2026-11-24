import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

from .models import Notification, User, UserNotification

logger = logging.getLogger(__name__)


def notification_payload(notification, user_notification):
    return {
        "id": str(user_notification.pk),
        "notification_id": str(notification.pk),
        "title": notification.title,
        "message": notification.message,
        "actor_id": str(notification.actor_id) if notification.actor_id else None,
        "is_read": user_notification.is_read,
        "created_at": (
            notification.created_at.isoformat() if notification.created_at else None
        ),
    }


def _publish(user_ids, notification, recipient_rows):
    payloads = {
        row.user_id: notification_payload(notification, row) for row in recipient_rows
    }

    def publish():
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                for user_id in user_ids:
                    async_to_sync(channel_layer.group_send)(
                        f"notifications.{user_id}",
                        {
                            "type": "notification.created",
                            "notification": payloads[user_id],
                        },
                    )
        except Exception:
            logger.exception("Failed to publish notification %s", notification.pk)

    transaction.on_commit(publish)


def create_notification(user, *, title, message, actor=None):
    """Create a notification for one recipient, optionally naming its actor."""
    if (
        not isinstance(user, User)
        or not user.pk
        or user._state.adding
        or not user.message_notifications
    ):
        return None
    notification = Notification.objects.create(
        title=title, message=message, actor=actor
    )
    recipient = UserNotification.objects.create(user=user, notification=notification)
    _publish([user.pk], notification, [recipient])
    return notification


def create_global_notification(*, title, message, actor=None):
    """Create shared content and a read receipt for every eligible active user."""
    users = User.objects.filter(
        is_active=True,
        status=User.Status.ACTIVE,
        message_notifications=True,
        deleted_at__isnull=True,
    ).only("pk")
    notification = Notification.objects.create(
        title=title, message=message, actor=actor, is_global=True
    )
    now = timezone.now()
    recipient_rows = [
        UserNotification(user_id=user.pk, notification=notification, created_at=now)
        for user in users.iterator(chunk_size=500)
    ]
    UserNotification.objects.bulk_create(recipient_rows, batch_size=500)
    _publish([row.user_id for row in recipient_rows], notification, recipient_rows)
    return notification
