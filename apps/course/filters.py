import django_filters

from .models import Course


class CourseFilter(django_filters.FilterSet):
    category = django_filters.UUIDFilter(field_name="categories__id", distinct=True)
    category_slug = django_filters.CharFilter(
        field_name="categories__slug", lookup_expr="iexact", distinct=True
    )
    tag = django_filters.UUIDFilter(field_name="tags__id", distinct=True)
    tag_slug = django_filters.CharFilter(
        field_name="tags__slug", lookup_expr="iexact", distinct=True
    )
    instructor = django_filters.UUIDFilter(field_name="instructor__id")
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Course
        fields = ("is_free", "is_best_seller")


class ManagementCourseFilter(CourseFilter):
    class Meta(CourseFilter.Meta):
        fields = (*CourseFilter.Meta.fields, "status")
