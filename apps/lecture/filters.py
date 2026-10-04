import django_filters

from .models import Lecture


class LectureFilter(django_filters.FilterSet):
    course = django_filters.UUIDFilter(field_name="course__id")
    course_slug = django_filters.CharFilter(
        field_name="course__slug", lookup_expr="iexact"
    )
    section = django_filters.UUIDFilter(field_name="section__id")
    section_slug = django_filters.CharFilter(
        field_name="section__slug", lookup_expr="iexact"
    )
    instructor = django_filters.UUIDFilter(field_name="instructor__id")

    class Meta:
        model = Lecture
        fields = ("status", "lecture_type", "is_preview")
