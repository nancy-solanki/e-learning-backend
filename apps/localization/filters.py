import django_filters

from .models import Localization


class LocalizationFilter(django_filters.FilterSet):
    language_name = django_filters.CharFilter(lookup_expr="iexact")
    country = django_filters.CharFilter(lookup_expr="iexact")
    is_deleted = django_filters.BooleanFilter(
        field_name="deleted_at", lookup_expr="isnull", exclude=True
    )

    class Meta:
        model = Localization
        fields = ("language_name", "country", "is_deleted")
