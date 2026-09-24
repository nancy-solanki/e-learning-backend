from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permission import IsInstructorOrAdmin
from apps.course.models import Course

from .serializers import FilteredSectionSerializer, SectionSerializer
from .service import SectionService

# Create your views here


@extend_schema_view(
    list=extend_schema(
        tags=["Section"],
        description="List all published sections with active instructors.",
    ),
    retrieve=extend_schema(
        tags=["Section"], description="Retrieve a specific published section by ID."
    ),
)
class SectionViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = SectionService.get_public_queryset()
    serializer_class = FilteredSectionSerializer
    lookup_field = "id"
    http_method_names = ["get", "head", "option"]


@extend_schema_view(
    list=extend_schema(
        tags=["Section"],
        description=(
            "List all sections for the authenticated instructor or all sections "
            "for admins."
        ),
    ),
    retrieve=extend_schema(
        tags=["Section"], description="Retrieve a specific section by ID."
    ),
    create=extend_schema(tags=["Section"], description="Create a new section."),
    update=extend_schema(tags=["Section"], description="Update a section."),
    partial_update=extend_schema(
        tags=["Section"], description="Partially update a section."
    ),
    destroy=extend_schema(
        tags=["Section"], description="Toggle the soft delete status of a section."
    ),
)
class AllSectionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsInstructorOrAdmin, IsAuthenticated]
    serializer_class = SectionSerializer

    def get_queryset(self, *args, **kwargs):
        return SectionService.get_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        SectionService.toggle_section_status(instance)
        if instance.deleted_at:
            return Response(
                {"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"message": "Activated successfully"}, status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Section"],
    description="Retrieve all sections belonging to a specific course slug.",
)
class SectionByCourseView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, slug):
        try:
            course = (
                Course.objects.filter(deleted_at__isnull=True)
                .filter(instructor__status="AC")
                .get(slug=slug)
            )
            return SectionService.get_sections_by_course(course)
        except Course.DoesNotExist:
            raise Http404

    def get(self, request, slug, format=None):
        section = self.get_object(slug)
        serializer = SectionSerializer(section, many=True)
        return Response(serializer.data)
