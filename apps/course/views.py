from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.category.models import Category
from apps.core.moderation import AdminStatusOnlyMixin, InstructorSubmissionMixin
from apps.core.permission import IsInstructorOrAdmin, IsSuperuserOrReadOnly
from apps.core.schema import MessageSerializer
from apps.localization.models import Localization
from apps.localization.serializers import LocalizationSerializer

from .filters import CourseFilter, ManagementCourseFilter
from .models import Course, Tag
from .serializers import (
    CourseResponseSerializer,
    CourseSerializer,
    FilteredCourseSerializer,
    InstructorCourseResponseSerializer,
    TagSerializer,
)
from .service import CourseService

# Create your views here.


@extend_schema(
    tags=["Course"], description="List active localizations for course selection."
)
class CourseLocalizationListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = LocalizationSerializer
    queryset = Localization.objects.filter(deleted_at__isnull=True).order_by(
        "language_name", "country", "id"
    )


@extend_schema(
    tags=["Course"],
    description="List active tags for instructor course selection.",
)
class CourseTagListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = TagSerializer
    queryset = Tag.objects.none()

    def get_queryset(self):
        queryset = Tag.objects.filter(deleted_at__isnull=True)
        if not getattr(self.request.user, "is_admin", False):
            queryset = queryset.filter(
                courses__instructor=self.request.user,
                courses__deleted_at__isnull=True,
            )
        return queryset.distinct().order_by("name", "id")


class CourseFilteringMixin:
    search_fields = [
        "title",
        "short_description",
        "long_description",
        "categories__title",
        "tags__name",
        "instructor__first_name",
        "instructor__last_name",
        "requirements",
        "learn_description_points",
    ]
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = CourseFilter
    ordering_fields = ("title", "price", "created_at", "updated_at")
    ordering = ("-created_at", "-id")


@extend_schema_view(
    list=extend_schema(
        tags=["Course"],
        description=(
            "List courses within this endpoint’s visibility scope. Public endpoints "
            "return published courses; management endpoints enforce instructor/admin access."
        ),
    ),
    retrieve=extend_schema(
        tags=["Course"], description="Retrieve a specific course by ID."
    ),
)
class CourseViewSet(CourseFilteringMixin, viewsets.ModelViewSet):
    permission_classes = (IsSuperuserOrReadOnly,)
    serializer_class = FilteredCourseSerializer
    queryset = Course.objects.none()
    lookup_field = "slug"
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        return CourseService.get_public_queryset()


@extend_schema_view(
    get=extend_schema(
        tags=["Course"],
        description=(
            "Retrieve a list of courses associated with a specific category, "
            "identified by its slug. Only courses belonging to active (non-deleted) "
            "categories are returned. The response includes filtered course data "
            "based on the requesting user's context."
        ),
    ),
)
class CourseByCategoryView(CourseFilteringMixin, ListAPIView):
    serializer_class = FilteredCourseSerializer
    queryset = Course.objects.none()
    permission_classes = [AllowAny]

    def get_queryset(self):
        category = Category.objects.filter(
            deleted_at__isnull=True, slug=self.kwargs["slug"]
        ).first()
        if not category:
            raise Http404
        return CourseService.get_courses_by_category(category)


@extend_schema_view(
    list=extend_schema(
        responses=CourseResponseSerializer(many=True),
        tags=["Course"],
        description=(
            "List courses within this endpoint’s visibility scope. Public endpoints "
            "return published courses; management endpoints enforce instructor/admin access."
        ),
    ),
    retrieve=extend_schema(
        responses=CourseResponseSerializer,
        tags=["Course"],
        description="Retrieve a specific course by ID.",
    ),
    create=extend_schema(
        responses={201: CourseResponseSerializer},
        tags=["Course"],
        description=(
            "Create a course as an instructor. Ownership is assigned to the "
            "authenticated user."
        ),
    ),
    update=extend_schema(
        responses={200: CourseResponseSerializer},
        tags=["Course"],
        description=(
            "Instructors may edit their own course but must submit it for review "
            "before publication; admins may update only status."
        ),
    ),
    partial_update=extend_schema(
        responses={200: CourseResponseSerializer},
        tags=["Course"],
        description=(
            "Instructors may edit their own course but must submit it for review "
            "before publication; admins may update only status."
        ),
    ),
    destroy=extend_schema(
        responses={200: MessageSerializer, 204: None},
        tags=["Course"],
        description=(
            "Admins soft-delete idempotently without restoring; "
            "instructors toggle soft deletion."
        ),
    ),
)
class AllCourseViewSet(
    InstructorSubmissionMixin,
    AdminStatusOnlyMixin,
    CourseFilteringMixin,
    viewsets.ModelViewSet,
):
    submission_label = "Course"
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = CourseSerializer
    queryset = Course.objects.none()
    filterset_class = ManagementCourseFilter

    @extend_schema(
        responses=InstructorCourseResponseSerializer(many=True),
        parameters=[
            OpenApiParameter(
                "category", OpenApiTypes.UUID, description="Filter by category ID."
            ),
            OpenApiParameter(
                "category_slug",
                OpenApiTypes.STR,
                description="Filter by category slug (case-insensitive).",
            ),
            OpenApiParameter("tag", OpenApiTypes.UUID, description="Filter by tag ID."),
            OpenApiParameter(
                "tag_slug",
                OpenApiTypes.STR,
                description="Filter by tag slug (case-insensitive).",
            ),
            OpenApiParameter(
                "price_min",
                OpenApiTypes.NUMBER,
                description="Minimum course price, inclusive.",
            ),
            OpenApiParameter(
                "price_max",
                OpenApiTypes.NUMBER,
                description="Maximum course price, inclusive.",
            ),
            OpenApiParameter(
                "is_free", OpenApiTypes.BOOL, description="Filter free courses."
            ),
            OpenApiParameter(
                "is_best_seller", OpenApiTypes.BOOL, description="Filter best sellers."
            ),
            OpenApiParameter(
                "status", OpenApiTypes.STR, description="Filter by course status."
            ),
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                description=(
                    "Search course title, descriptions, categories, tags, instructor name, "
                    "requirements, and learning points."
                ),
            ),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description=(
                    "Order by title, price, created_at, or updated_at; prefix with '-' "
                    "for descending order."
                ),
            ),
            OpenApiParameter(
                "page",
                OpenApiTypes.INT,
                description="Page number (20 records per page).",
            ),
        ],
        description=(
            "List courses in the authenticated user's management scope. Instructors "
            "see their own courses; admins see all courses. Filters are applied "
            "within that scope. The response is paginated with count, next, previous, "
            "and results fields."
        ),
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        return CourseService.get_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    def _destroy_instructor(self, request, *args, **kwargs):
        instance = self.get_object()
        CourseService.toggle_course_status(instance)
        if instance.is_deleted:
            return Response(
                {"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"message": "Activated successfully"}, status=status.HTTP_200_OK
        )
