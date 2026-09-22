import django_filters
from .models import Bank


class BankFilter(django_filters.FilterSet):
    default = django_filters.BooleanFilter(field_name='default')

    class Meta:
        model = Bank
        fields = ['default']
