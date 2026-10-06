from django.db.models import Q
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .filters import EnrollFilter
from .models import Enroll
from .serializers import EnrollSerializer
from .service import EnrollService


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
    )
    ordering_fields = ("created_at", "user__first_name", "user__last_name")
    ordering = ("-created_at",)


@extend_schema_view(
    list=extend_schema(
        tags=["Enrollment"],
        description=(
            "List all enrollments based on user role. Instructors see enrollments "
            "for their courses, regular users see their own. Supports search and "
            "filtering by course UUID, course slug, user UUID, and inclusive "
            "creation dates (created_at_after / created_at_before). Search by "
            "username, name, email, or course title."
        ),
    ),
    retrieve=extend_schema(
        tags=["Enrollment"], description="Retrieve a specific enrollment by its UUID."
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
        enrollments = EnrollService.get_enrollments_by_course(
            self.kwargs["slug"]
        ).filter(Q(user=self.request.user) | Q(course__instructor=self.request.user))
        if not enrollments.exists():
            raise Http404
        return enrollments
