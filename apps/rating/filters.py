import django_filters

from .models import Rating


class RatingFilter(django_filters.FilterSet):
    course = django_filters.UUIDFilter(field_name="course__id")
    user = django_filters.UUIDFilter(field_name="user__id")
    rating_min = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")
    rating_max = django_filters.NumberFilter(field_name="rating", lookup_expr="lte")
    created_at_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_at_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Rating
        fields = ["course", "user", "rating"]
