from rest_framework import serializers

from .models import Localization


class LocalizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localization
        fields = (
            "id",
            "language_name",
            "country",
            "created_at",
            "updated_at",
            "deleted_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "deleted_at")
