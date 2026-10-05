import django_filters

from .models import Enroll


class EnrollFilter(django_filters.FilterSet):
    course = django_filters.UUIDFilter(field_name="course__id")
    user = django_filters.UUIDFilter(field_name="user__id")
    course_slug = django_filters.CharFilter(
        field_name="course__slug", lookup_expr="iexact"
    )
    created_at_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_at_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Enroll
        fields = ["course", "user", "course_slug"]
