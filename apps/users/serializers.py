from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    """
    Base serializer with common user fields and methods.
    """

    role = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()

    def get_role(self, obj):
        return [group.name for group in obj.groups.all()]

    def get_gender(self, obj):
        return obj.get_gender_display()


class UserProfileSerializer(BaseUserSerializer):
    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "username",
            "phone_number",
            "avatar",
            "birth_date",
            "gender",
            "email_notifications",
            "account_activity",
            "message_notifications",
            "role",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not instance.groups.filter(name__in=("instructor", "admin")).exists():
            representation.pop("role", None)
        return representation


class UserSerializer(BaseUserSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "username",
            "phone_number",
            "avatar",
            "birth_date",
            "gender",
            "email_notifications",
            "account_activity",
            "message_notifications",
            "role",
            "status",
            "last_login",
            "created_at",
            "updated_at",
            "deleted_at",
            "password_changed_at",
        ]

    def get_status(self, obj):
        return obj.get_status_display()
