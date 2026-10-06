from rest_framework import serializers

from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    course_title = serializers.SerializerMethodField("get_course_title")

    def get_course_title(self, instance) -> str | None:
        return instance.course.title if instance.course else None

    class Meta:
        model = Coupon
        fields = "__all__"
