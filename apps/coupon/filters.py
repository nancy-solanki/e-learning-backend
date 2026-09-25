import django_filters

from .models import Coupon


class CouponFilter(django_filters.FilterSet):
    is_global = django_filters.BooleanFilter(field_name="is_global")
    coupon_type = django_filters.CharFilter(
        field_name="coupon_type", lookup_expr="iexact"
    )
    course = django_filters.UUIDFilter(field_name="course__id")
    is_unlimited = django_filters.BooleanFilter(field_name="is_unlimited")
    is_instructor_created = django_filters.BooleanFilter(
        field_name="is_instructor_created"
    )

    class Meta:
        model = Coupon
        fields = [
            "is_global",
            "coupon_type",
            "course",
            "is_unlimited",
            "is_instructor_created",
        ]
