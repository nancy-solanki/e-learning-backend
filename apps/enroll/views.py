import csv

from django.db.models import Q
from django.http import Http404, HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiTypes,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permission import IsSuperuser
from apps.course.models import Course

from .filters import EnrollFilter
from .models import Enroll
from .serializers import (
    AdminEnrollmentSerializer,
    EnrollmentCourseSerializer,
    EnrollmentSummarySerializer,
    EnrollSerializer,
)
from .service import EnrollService


def csv_value(value):
    text = str(value) if value is not None else ""
    # Prevent spreadsheet applications interpreting user-controlled text as formulas.
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(
        ("\t", "\r", "\n")
    ):
        return "'" + text
    return text


class EnrollmentFilteringMixin:
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = EnrollFilter
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "course__title",
        "id",
    )
    ordering_fields = ("created_at", "user__first_name", "user__last_name")
    ordering = ("-created_at", "-id")


@extend_schema_view(
    list=extend_schema(
        tags=["Enrollment"],
        responses=PolymorphicProxySerializer(
            component_name="RoleEnrollment",
            serializers=[EnrollSerializer, AdminEnrollmentSerializer],
            resource_type_field_name=None,
        ),
        description=(
            "List enrollments by role: admins see all active enrollments and learner email. "
            "Instructors see enrollments "
            "for their courses, regular users see their own. Supports search and "
            "filtering by course UUID, course slug, user UUID, and inclusive "
            "creation dates (created_at_after / created_at_before). Search by "
            "username, name, email, course title, or enrollment UUID."
        ),
    ),
    retrieve=extend_schema(
        tags=["Enrollment"],
        description="Retrieve an enrollment within the caller role scope.",
        responses=PolymorphicProxySerializer(
            component_name="RoleEnrollment",
            serializers=[EnrollSerializer, AdminEnrollmentSerializer],
            resource_type_field_name=None,
        ),
    ),
)
class EnrollViewSet(EnrollmentFilteringMixin, viewsets.ModelViewSet):
    """
    ViewSet for listing and retrieving enrollments.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EnrollSerializer
    queryset = Enroll.objects.none()
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        """
        Return the enrollments based on the current user role.
        """
        return EnrollService.get_enrollments(self.request.user)

    def get_serializer_class(self):
        if (
            self.action in ("list", "retrieve")
            and not getattr(self, "swagger_fake_view", False)
            and self.request.user.is_admin
        ):
            return AdminEnrollmentSerializer
        return super().get_serializer_class()

    @extend_schema(responses=EnrollmentSummarySerializer)
    @action(detail=False, pagination_class=None, permission_classes=[IsSuperuser])
    def summary(self, request):
        """Counts across all matching records, independent of pagination."""
        count = self.filter_queryset(self.get_queryset()).count()
        return Response(
            {
                "total_enrollments": count,
                "in_progress": None,
                "completed": None,
                "not_started": None,
                "unknown": count,
                "progress_tracking_available": False,
            }
        )

    @extend_schema(responses=EnrollmentCourseSerializer(many=True), filters=False)
    @action(
        detail=False,
        filter_backends=[],
        serializer_class=EnrollmentCourseSerializer,
        permission_classes=[IsSuperuser],
    )
    def courses(self, request):
        """Paginated course options with at least one active enrollment."""
        courses = (
            Course.objects.filter(pk__in=self.get_queryset().values("course_id"))
            .distinct()
            .order_by("title", "id")
        )
        page = self.paginate_queryset(courses)
        if page is not None:
            return self.get_paginated_response(
                self.get_serializer(page, many=True).data
            )
        return Response(self.get_serializer(courses, many=True).data)

    @extend_schema(responses={(200, "text/csv"): OpenApiTypes.STR})
    @action(detail=False, pagination_class=None, permission_classes=[IsSuperuser])
    def export(self, request):
        """Export all matching enrollments as CSV, ignoring pagination."""
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="enrollments.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Enrollment ID",
                "Student",
                "Email",
                "Course",
                "Enrolled on",
                "Total lessons",
                "Completed lessons",
                "Progress (%)",
                "Status",
                "Access",
            ]
        )
        for enrollment in self.filter_queryset(self.get_queryset()).iterator(
            chunk_size=500
        ):
            writer.writerow(
                map(
                    csv_value,
                    [
                        enrollment.pk,
                        enrollment.user.get_full_name(),
                        enrollment.user.email,
                        enrollment.course.title,
                        (
                            enrollment.created_at.isoformat()
                            if enrollment.created_at
                            else None
                        ),
                        enrollment.total_lessons,
                        None,
                        None,
                        "unknown",
                        None,
                    ],
                )
            )
        return response


@extend_schema_view(
    get=extend_schema(
        tags=["Enrollment"],
        description=(
            "Retrieve active enrollments for a published course by slug. Students see "
            "only their own enrollment; the course instructor sees the roster. Supports "
            "search by username, name, email, or course title; filtering by course "
            "UUID, course slug, user UUID, and inclusive creation dates "
            "(created_at_after / created_at_before); and ordering."
        ),
    ),
)
class EnrollByCourseView(EnrollmentFilteringMixin, ListAPIView):
    """
    API View to retrieve enrollments associated with a specific course slug.
    Only active enrollments for published courses are returned.
    """

    serializer_class = EnrollSerializer
    queryset = Enroll.objects.none()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve enrollments for a course by slug.
        """
        enrollments = EnrollService.get_enrollments_by_course(self.kwargs["slug"])
        if not self.request.user.is_admin:
            enrollments = enrollments.filter(
                Q(user=self.request.user) | Q(course__instructor=self.request.user)
            )
        if not enrollments.exists():
            raise Http404
        return enrollments
