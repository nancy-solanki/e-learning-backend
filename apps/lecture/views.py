from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.permission import IsInstructorOrAdmin
from apps.core.schema import MessageSerializer

from .filters import LectureFilter
from .models import Lecture
from .repository import LectureRepository
from .serializers import LectureSerializer
from .service import LectureService


class LectureFilteringMixin:
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = LectureFilter
    search_fields = ("title", "description", "course__title", "section__title")
    ordering_fields = ("order", "title", "created_at", "updated_at")
    ordering = ("order", "-created_at", "id")


@extend_schema_view(
    list=extend_schema(
        tags=["Lecture"],
        description="List all active lectures. Available for public view.",
    ),
    retrieve=extend_schema(
        tags=["Lecture"], description="Retrieve a specific lecture by its ID."
    ),
)
class LectureViewSet(LectureFilteringMixin, viewsets.ModelViewSet):
    """
    ViewSet for public-facing lecture listing and detail.
    """

    permission_classes = [AllowAny]
    queryset = LectureRepository.get_active_lectures()
    serializer_class = LectureSerializer
    lookup_field = "id"
    http_method_names = ["get", "head", "options"]


@extend_schema_view(
    list=extend_schema(
        tags=["Lecture"],
        description="List all lectures for management. Admin sees all, instructors see their own.",
    ),
    retrieve=extend_schema(
        tags=["Lecture"], description="Retrieve a specific lecture for management."
    ),
    create=extend_schema(
        tags=["Lecture"],
        description="Create a new lecture. Handles video processing and course updates.",
    ),
    update=extend_schema(tags=["Lecture"], description="Update a lecture."),
    partial_update=extend_schema(
        tags=["Lecture"], description="Partially update a lecture."
    ),
    destroy=extend_schema(
        responses={200: MessageSerializer},
        tags=["Lecture"],
        description="Toggle deletion status (soft delete/restore) for a lecture.",
    ),
)
class AllLectureViewSet(LectureFilteringMixin, viewsets.ModelViewSet):
    """
    ViewSet for administrator and instructor to manage all lectures.
    """

    permission_classes = [IsInstructorOrAdmin, IsAuthenticated]
    serializer_class = LectureSerializer

    queryset = Lecture.objects.none()

    def get_queryset(self):
        if self.request.user.is_admin:
            return LectureRepository.get_admin_lectures()
        return LectureRepository.get_instructor_lectures(self.request.user)

    def perform_create(self, serializer):
        # We let the service handle the creation logic including video processing
        # and course/section updates.
        serializer.instance = LectureService.create_lecture(
            user=self.request.user, validated_data=serializer.validated_data
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        message = LectureService.toggle_lecture_status(instance)
        # Check if it was a deletion or activation for status code
        if "activated" in message:
            return Response({"message": message}, status=status.HTTP_200_OK)
        return Response({"message": message}, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        tags=["Lecture"],
        description="Retrieve all lectures belonging to a specific section slug.",
    ),
)
class LectureBySectionView(LectureFilteringMixin, ListAPIView):
    """
    API View to retrieve lectures associated with a specific section.
    """

    serializer_class = LectureSerializer
    permission_classes = [AllowAny]

    queryset = Lecture.objects.none()

    def get_queryset(self):
        lectures = LectureRepository.get_lectures_by_section_slug(self.kwargs["slug"])
        if not lectures.exists():
            raise Http404
        return lectures
