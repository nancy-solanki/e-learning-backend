from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permission import IsOwnerOrInstructor

from .serializers import RatingSerializer
from .service import RatingService


@extend_schema_view(
    list=extend_schema(
        tags=["Rating"],
        description="List all ratings. Instructors see ratings for their courses.",
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
class RatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ratings.
    """

    permission_classes = [IsAuthenticated, IsOwnerOrInstructor]
    serializer_class = RatingSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    search_fields = [
        "course__title",
        "comment",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__username",
    ]

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
        description="Retrieve all ratings for courses where the user is an instructor.",
    ),
)
class RatingByInstructorView(APIView):
    """
    API View to retrieve ratings for courses taught by the current instructor.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        ratings = RatingService.get_instructor_course_ratings(request.user)
        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
