import django_filters
from django.db.models import Q

from .models import Enroll


class EnrollFilter(django_filters.FilterSet):
    """
    Filter for enrollments with support for searching by user name/email
    and filtering by course.
    """

    search = django_filters.CharFilter(method="filter_search")
    course = django_filters.UUIDFilter(field_name="course__id")

    class Meta:
        model = Enroll
        fields = ["course"]

    def filter_search(self, queryset, name, value):
        """
        Search by user first name, last name, email, or course title.
        """
        if value:
            return queryset.filter(
                Q(user__first_name__icontains=value)
                | Q(user__last_name__icontains=value)
                | Q(user__email__icontains=value)
                | Q(course__title__icontains=value)
            )
        return queryset
