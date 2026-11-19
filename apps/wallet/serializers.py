from rest_framework import serializers

from apps.users.serializers import PublicUserSerializer

from .models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"


class WalletOptionSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)

    class Meta:
        model = Wallet
        fields = ("id", "user")
        read_only_fields = fields
