from rest_framework import serializers

from .models import UserNotification


class NotificationSerializer(serializers.ModelSerializer):
    notification_id = serializers.UUIDField(read_only=True)
    title = serializers.CharField(source="notification.title", read_only=True)
    message = serializers.CharField(source="notification.message", read_only=True)
    actor_id = serializers.UUIDField(source="notification.actor_id", read_only=True)
    is_global = serializers.BooleanField(
        source="notification.is_global", read_only=True
    )

    class Meta:
        model = UserNotification
        fields = (
            "id",
            "notification_id",
            "title",
            "message",
            "actor_id",
            "is_global",
            "is_read",
            "read_at",
            "created_at",
        )
        read_only_fields = fields
