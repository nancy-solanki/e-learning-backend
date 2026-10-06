from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.core.permission import IsOwnerOrInstructor

from .filters import RatingFilter
from .models import Rating
from .serializers import RatingSerializer
from .service import RatingService


class RatingFilteringMixin:
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = RatingFilter
    search_fields = (
        "course__title",
        "comment",
        "response",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__username",
    )
    ordering_fields = ("created_at", "rating")
    ordering = ("-created_at",)


RATING_FILTER_DESCRIPTION = (
    " Filter by course/user UUID, exact rating, rating_min/max, or inclusive "
    "creation dates (created_at_after/before). Search by course title, comment, "
    "instructor response, or reviewer name, email, or username. Order by "
    "created_at or rating (prefix with '-' for descending)."
)


@extend_schema_view(
    list=extend_schema(
        tags=["Rating"],
        description="List all ratings. Instructors see ratings for their courses."
        + RATING_FILTER_DESCRIPTION,
    ),
    retrieve=extend_schema(
        tags=["Rating"], description="Retrieve a specific rating by UUID."
    ),
    create=extend_schema(
        tags=["Rating"], description="Create a new rating for a course."
    ),
    update=extend_schema(
        tags=["Rating"], description="Update a rating (instructor or owner)."
    ),
    partial_update=extend_schema(
        tags=["Rating"], description="Partial update of a rating (instructor or owner)."
    ),
    destroy=extend_schema(tags=["Rating"], description="Soft delete a rating."),
)
class RatingViewSet(RatingFilteringMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing ratings.
    """

    permission_classes = [IsAuthenticated, IsOwnerOrInstructor]
    serializer_class = RatingSerializer
    queryset = Rating.objects.none()

    def get_queryset(self):
        return RatingService.get_ratings(self.request.user)

    def perform_create(self, serializer):
        serializer.instance = RatingService.add_rating(
            user=self.request.user, validated_data=serializer.validated_data
        )

    def perform_destroy(self, instance):
        instance.soft_delete()


@extend_schema_view(
    get=extend_schema(
        tags=["Rating"],
        description="Retrieve all ratings for courses where the user is an instructor."
        + RATING_FILTER_DESCRIPTION,
    ),
)
class RatingByInstructorView(RatingFilteringMixin, ListAPIView):
    """
    API View to retrieve ratings for courses taught by the current instructor.
    """

    serializer_class = RatingSerializer
    queryset = Rating.objects.none()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RatingService.get_instructor_course_ratings(self.request.user)
