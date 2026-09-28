import django_filters

from .models import User


class UserFilter(django_filters.FilterSet):
    STATUS_VALUES = {
        "active": User.Status.ACTIVE,
        "inactive": User.Status.INACTIVE,
        "suspended": User.Status.SUSPEND,
        "pending": User.Status.PENDING,
    }

    status = django_filters.ChoiceFilter(
        choices=[(value, value) for value in STATUS_VALUES],
        method="filter_status",
    )

    def filter_status(self, queryset, name, value):
        return queryset.filter(status=self.STATUS_VALUES[value])

    class Meta:
        model = User
        fields = ["status"]
