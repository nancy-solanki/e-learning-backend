from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from apps.users.serializers import PublicUserSerializer

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")


@extend_schema_serializer(many=False)
class AdminTransactionSerializer(TransactionSerializer):
    """Transaction details with the owner expanded for the admin panel."""

    user = PublicUserSerializer(read_only=True)


class TransactionPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = AdminTransactionSerializer(many=True)
