from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.moderation import AdminStatusOnlyMixin, InstructorSubmissionMixin
from apps.core.permission import IsInstructorOrAdmin
from apps.core.schema import MessageSerializer
from apps.course.models import Course

from .filters import SectionFilter
from .models import Section
from .serializers import FilteredSectionSerializer, SectionSerializer
from .service import SectionService


class SectionFilteringMixin:
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = SectionFilter
    search_fields = ("title", "description", "course__title")
    ordering_fields = ("order", "title", "created_at", "updated_at")
    ordering = ("order", "-created_at", "id")


@extend_schema_view(
    list=extend_schema(
        tags=["Section"],
        description="List all published sections with active instructors.",
    ),
    retrieve=extend_schema(
        tags=["Section"], description="Retrieve a specific published section by ID."
    ),
)
class SectionViewSet(SectionFilteringMixin, viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = SectionService.get_public_queryset()
    serializer_class = FilteredSectionSerializer
    lookup_field = "id"
    http_method_names = ["get", "head", "options"]


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
    create=extend_schema(
        tags=["Section"], description="Create a new section as a non-admin instructor."
    ),
    update=extend_schema(
        tags=["Section"],
        description=(
            "Instructors may edit their own section but must submit it for review "
            "before publication; admins may update only status."
        ),
    ),
    partial_update=extend_schema(
        tags=["Section"],
        description=(
            "Instructors may edit their own section but must submit it for review "
            "before publication; admins may update only status."
        ),
    ),
    destroy=extend_schema(
        responses={200: MessageSerializer, 204: None},
        tags=["Section"],
        description=(
            "Admins soft-delete idempotently without restoring; "
            "instructors toggle soft deletion."
        ),
    ),
)
class AllSectionViewSet(
    InstructorSubmissionMixin,
    AdminStatusOnlyMixin,
    SectionFilteringMixin,
    viewsets.ModelViewSet,
):
    submission_label = "Section"
    permission_classes = [IsInstructorOrAdmin, IsAuthenticated]
    serializer_class = SectionSerializer

    queryset = Section.objects.none()

    def get_queryset(self, *args, **kwargs):
        return SectionService.get_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    def validate_submission(self, instance):
        super().validate_submission(instance)
        if not instance.lecture.filter(deleted_at__isnull=True).exists():
            raise ValidationError(
                {
                    "detail": (
                        "Add at least one non-deleted lecture before submitting "
                        "this section for review."
                    )
                }
            )

    def _destroy_instructor(self, request, *args, **kwargs):
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
class SectionByCourseView(SectionFilteringMixin, ListAPIView):
    serializer_class = SectionSerializer
    permission_classes = [AllowAny]

    queryset = Section.objects.none()

    def get_queryset(self):
        try:
            course = (
                Course.objects.filter(deleted_at__isnull=True)
                .filter(instructor__status="AC")
                .filter(status="published")
                .get(slug=self.kwargs["slug"])
            )
            return SectionService.get_published_sections_by_course(course)
        except Course.DoesNotExist:
            raise Http404
