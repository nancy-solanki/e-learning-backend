import django_filters

from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    wallet = django_filters.UUIDFilter(field_name="wallet__id")
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    created_at_after = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__gte"
    )
    created_at_before = django_filters.DateFilter(
        field_name="created_at", lookup_expr="date__lte"
    )

    class Meta:
        model = Transaction
        fields = ["status", "transaction_type", "wallet", "tx_id"]
