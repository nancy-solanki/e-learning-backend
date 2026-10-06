"""Response models for fields transformed by to_representation."""

from rest_framework import serializers

from .serializers import UserProfileSerializer, UserSerializer


class UserResponseSerializer(UserSerializer):
    gender = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class UserProfileResponseSerializer(UserProfileSerializer):
    gender = serializers.CharField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    avatar = serializers.URLField(read_only=True, allow_null=True)
