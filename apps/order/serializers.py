from rest_framework import serializers

from apps.course.serializers import CourseSerializer
from apps.users.serializers import PublicUserSerializer

from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    user = PublicUserSerializer(read_only=True)
    instructor = PublicUserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
