from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.common.service import FileService

User = get_user_model()


class BaseUserSerializer(serializers.ModelSerializer):
    """
    Base serializer with common user fields and methods.
    """

    avatar = serializers.URLField(read_only=True)
    role = serializers.SerializerMethodField()

    def get_role(self, obj) -> list[str]:
        return [group.name for group in obj.groups.all()]

    def validate_full_name(self, value):
        names = value.split(None, 1)
        if any(len(name) > 200 for name in names):
            raise serializers.ValidationError(
                "First and last names must each be at most 200 characters."
            )
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["gender"] = instance.get_gender_display()
        return data


class UserProfileSerializer(BaseUserSerializer):
    full_name = serializers.CharField(required=False)
    avatar = serializers.ImageField(required=False, allow_null=True, write_only=True)
    gender = serializers.ChoiceField(choices=User.Gender.choices, required=False)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "phone_number",
            "avatar",
            "birth_date",
            "gender",
            "email_notifications",
            "public_profile",
            "search_engine_visibility",
            "share_learning_activity",
            "role",
            "language",
            "bio",
            "full_name",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["full_name"] = f"{instance.first_name} {instance.last_name}".strip()
        data["avatar"] = instance.avatar or None
        return data

    def update(self, instance, validated_data):
        full_name = validated_data.pop("full_name", None)
        if full_name:
            names = full_name.split(None, 1)
            instance.first_name = names[0]
            instance.last_name = names[1] if len(names) > 1 else ""

        if "avatar" in validated_data:
            avatar = validated_data.pop("avatar")
            if avatar is None:
                instance.avatar = ""
            else:
                try:
                    file_obj = FileService.upload_file_to_cloud(avatar, "avatars")
                except ValueError as exc:
                    raise serializers.ValidationError({"avatar": str(exc)}) from exc
                instance.avatar = file_obj.url

        return super().update(instance, validated_data)


class UserSerializer(BaseUserSerializer):
    status = serializers.SerializerMethodField()
    full_name = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "phone_number",
            "avatar",
            "birth_date",
            "gender",
            "email_notifications",
            "public_profile",
            "search_engine_visibility",
            "share_learning_activity",
            "role",
            "status",
            "language",
            "bio",
            "full_name",
            "last_login",
            "created_at",
            "updated_at",
            "deleted_at",
            "password_changed_at",
        ]

    def get_status(self, obj) -> str:
        return obj.get_status_display()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["full_name"] = f"{instance.first_name} {instance.last_name}".strip()
        return data

    def update(self, instance, validated_data):
        full_name = validated_data.pop("full_name", None)
        if full_name:
            names = full_name.split(None, 1)
            instance.first_name = names[0]
            instance.last_name = names[1] if len(names) > 1 else ""

        return super().update(instance, validated_data)


class PublicUserSerializer(serializers.ModelSerializer):
    """Identity safe to embed in another user's resource representation."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "full_name", "avatar")
        read_only_fields = fields

    def get_full_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}".strip()
