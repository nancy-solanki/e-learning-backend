from datetime import datetime

from dj_rest_auth.registration.serializers import (
    SocialLoginSerializer as BaseSocialLoginSerializer,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import Group
from django.utils.encoding import DjangoUnicodeDecodeError, smart_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .services import (
    account_activation_token,
    password_reset_token,
    send_reset_password_email,
    send_verify_email,
)

User = get_user_model()


class SocialLoginSerializer(BaseSocialLoginSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        user = attrs["user"]
        group, _ = Group.objects.get_or_create(name="student")
        user.groups.add(group)
        if user.status != User.Status.ACTIVE:
            user.status = User.Status.ACTIVE
            user.save(update_fields=("status",))
        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "username", "first_name", "last_name", "password")
        extra_kwargs = {
            "username": {"required": True},
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        group, _ = Group.objects.get_or_create(name="student")
        user.save()
        user.groups.add(group)
        try:
            send_verify_email(user)
        except Exception:
            # Ensure account creation is not blocked by email send issues
            # These are logged in send_email_with_context
            pass
        return user


class UserActivateAccountSerializer(serializers.Serializer):

    def validate(self, attrs):
        try:
            uid = self.context.get("uid")
            token = self.context.get("token")
            user = User.objects.get(id=smart_str(urlsafe_base64_decode(uid)))

            if not account_activation_token.check_token(user, token):
                raise serializers.ValidationError("Token is not valid or expired")

            user.status = User.Status.ACTIVE
            user.save()
            return attrs
        except (DjangoUnicodeDecodeError, ValueError, User.DoesNotExist):
            raise serializers.ValidationError("Activation link is invalid or expired")


class UserLogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(max_length=500)

    def validate(self, attrs):
        self.token = attrs.get("refresh_token")
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"errors": {"bad_token": "Token is invalid or expired"}}
            )


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )
    new_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    class Meta:
        fields = ["old_password", "new_password"]

    def validate(self, attrs):
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")

        user = self.context.get("user")

        if not check_password(old_password, user.password):
            raise serializers.ValidationError("Your password was incorrect.")

        user.password_changed_at = datetime.now()
        user.set_password(new_password)
        user.save()
        return attrs


class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email").lower()

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)

            if user.status == User.Status.PENDING:
                raise serializers.ValidationError(
                    {
                        "errors": {
                            "non_field_error": [
                                "Email is not verified. Please check your email inbox."
                            ]
                        }
                    }
                )
            elif user.status == User.Status.SUSPEND:
                raise serializers.ValidationError(
                    {"errors": {"non_field_error": ["Account is not active"]}}
                )

            send_reset_password_email(user)
            return attrs
        raise serializers.ValidationError("Account with this email doesn't exists")


class UserPasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    class Meta:
        fields = ["password"]

    def validate(self, attrs):
        try:
            password = attrs.get("password")
            uid = self.context.get("uid")
            token = self.context.get("token")
            user = User.objects.get(id=smart_str(urlsafe_base64_decode(uid)))

            if not password_reset_token.check_token(user, token):
                raise serializers.ValidationError("Token is not valid or expired")

            user.password_changed_at = datetime.now()
            user.set_password(password)
            user.save()
            return attrs
        except (DjangoUnicodeDecodeError, ValueError):
            raise serializers.ValidationError("Token is not valid or expire")
