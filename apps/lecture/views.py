from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permission import IsInstructorOrAdmin

from .repository import LectureRepository
from .serializers import LectureSerializer
from .service import LectureService


@extend_schema_view(
    list=extend_schema(
        tags=["Lecture"],
        description="List all active lectures. Available for public view.",
    ),
    retrieve=extend_schema(
        tags=["Lecture"], description="Retrieve a specific lecture by its ID."
    ),
)
class LectureViewSet(viewsets.ModelViewSet):
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
        tags=["Lecture"],
        description="Toggle deletion status (soft delete/restore) for a lecture.",
    ),
)
class AllLectureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for administrator and instructor to manage all lectures.
    """

    permission_classes = [IsInstructorOrAdmin, IsAuthenticated]
    serializer_class = LectureSerializer

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
class LectureBySectionView(APIView):
    """
    API View to retrieve lectures associated with a specific section.
    """

    permission_classes = [AllowAny]

    def get_object(self, slug):
        lectures = LectureRepository.get_lectures_by_section_slug(slug)
        if not lectures.exists():
            raise Http404
        return lectures

    def get(self, request, slug, format=None):
        lecture = self.get_object(slug)
        serializer = LectureSerializer(lecture, many=True)
        return Response(serializer.data)
