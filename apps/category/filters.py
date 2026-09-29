import django_filters

from .models import Category


class CategoryFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="iexact")
    slug = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Category
        fields = ("title", "slug")
