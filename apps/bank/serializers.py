from rest_framework import serializers
from .models import Bank

class BankSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Bank
        fields = "__all__"
