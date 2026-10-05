import django_filters

from .models import Order


class OrderFilter(django_filters.FilterSet):
    course = django_filters.UUIDFilter(field_name="course__id")
    user = django_filters.UUIDFilter(field_name="user__id")
    instructor = django_filters.UUIDFilter(field_name="instructor__id")
    coupon = django_filters.UUIDFilter(field_name="coupon__id")
    total_paid_min = django_filters.NumberFilter(
        field_name="total_paid", lookup_expr="gte"
    )
    total_paid_max = django_filters.NumberFilter(
        field_name="total_paid", lookup_expr="lte"
    )
    created_at_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_at_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Order
        fields = ["status", "is_free", "course", "user", "instructor", "coupon"]
