import django_filters

from .models import Section


class SectionFilter(django_filters.FilterSet):
    course = django_filters.UUIDFilter(field_name="course__id")
    course_slug = django_filters.CharFilter(
        field_name="course__slug", lookup_expr="iexact"
    )
    instructor = django_filters.UUIDFilter(field_name="instructor__id")

    class Meta:
        model = Section
        fields = ("status",)
