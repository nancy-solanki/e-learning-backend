from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from .filters import EnrollFilter
from .serializers import EnrollSerializer
from .service import EnrollService


@extend_schema_view(
    list=extend_schema(
        tags=["Enrollment"],
        description=(
            "List all enrollments based on user role. Instructors see enrollments "
            "for their courses, regular users see their own. Supports search and "
            "filtering by course."
        ),
    ),
    retrieve=extend_schema(
        tags=["Enrollment"], description="Retrieve a specific enrollment by its UUID."
    ),
)
class EnrollViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and retrieving enrollments.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = EnrollSerializer
    http_method_names = ["get", "head", "options"]
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = EnrollFilter
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "course__title",
    )
    ordering_fields = ("created_at", "user__first_name", "user__last_name")
    ordering = ("-created_at",)

    def get_queryset(self):
        """
        Return the enrollments based on the current user role.
        """
        return EnrollService.get_enrollments(self.request.user)


@extend_schema_view(
    get=extend_schema(
        tags=["Enrollment"],
        description="Retrieve all enrollments associated with a specific course slug.",
    ),
)
class EnrollByCourseView(ListAPIView):
    """
    API View to retrieve enrollments associated with a specific course slug.
    Only active enrollments for published courses are returned.
    """

    serializer_class = EnrollSerializer
    filter_backends = ()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve enrollments for a course by slug.
        """
        enrollments = EnrollService.get_enrollments_by_course(self.kwargs["slug"])
        if not enrollments.exists():
            raise Http404
        return enrollments
