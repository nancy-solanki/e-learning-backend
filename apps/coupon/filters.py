import django_filters

from .models import Coupon


class CouponFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr="iexact")
    is_deleted = django_filters.BooleanFilter(
        field_name="deleted_at", lookup_expr="isnull", exclude=True
    )
    expired_at_after = django_filters.DateFilter(
        field_name="expired_at", lookup_expr="gte"
    )
    expired_at_before = django_filters.DateFilter(
        field_name="expired_at", lookup_expr="lte"
    )
    value_min = django_filters.NumberFilter(field_name="value", lookup_expr="gte")
    value_max = django_filters.NumberFilter(field_name="value", lookup_expr="lte")
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
