import django_filters

from .models import Wallet


class WalletFilter(django_filters.FilterSet):
    current_earnings_min = django_filters.NumberFilter(
        field_name="current_earnings", lookup_expr="gte"
    )
    current_earnings_max = django_filters.NumberFilter(
        field_name="current_earnings", lookup_expr="lte"
    )
    total_earnings_min = django_filters.NumberFilter(
        field_name="total_earnings", lookup_expr="gte"
    )
    total_earnings_max = django_filters.NumberFilter(
        field_name="total_earnings", lookup_expr="lte"
    )
    total_withdraws_min = django_filters.NumberFilter(
        field_name="total_withdraws", lookup_expr="gte"
    )
    total_withdraws_max = django_filters.NumberFilter(
        field_name="total_withdraws", lookup_expr="lte"
    )
    created_at_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_at_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Wallet
        fields = [
            "is_site_wallet",
            "current_earnings",
            "total_earnings",
            "total_withdraws",
        ]
