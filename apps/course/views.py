from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.category.models import Category
from apps.core.permission import IsInstructorOrAdmin, IsSuperuserOrReadOnly

from .serializers import CourseSerializer, FilteredCourseSerializer
from .service import CourseService

# Create your views here.


@extend_schema_view(
    list=extend_schema(
        tags=["Course"],
        description=(
            "List all courses. Superusers see all, other authenticated users "
            "see only active ones."
        ),
    ),
    retrieve=extend_schema(
        tags=["Course"], description="Retrieve a specific course by ID."
    ),
)
class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = (IsSuperuserOrReadOnly,)
    serializer_class = FilteredCourseSerializer
    search_fields = [
        "title",
        "short_description",
        "long_description",
        "requirements",
        "learn_description_points",
    ]
    filter_backends = (filters.SearchFilter,)
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
class CourseByCategoryView(APIView):
    permission_classes = [AllowAny]

    def get_object(self, slug):
        category = Category.objects.filter(deleted_at__isnull=True, slug=slug).first()
        if not category:
            raise Http404
        return CourseService.get_courses_by_category(category)

    def get(self, request, slug, format=None):
        course = self.get_object(slug)
        serializer = FilteredCourseSerializer(
            course, many=True, context={"request": request}
        )
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=["Course"],
        description=(
            "List all courses. Superusers see all, other authenticated users "
            "see only active ones."
        ),
    ),
    retrieve=extend_schema(
        tags=["Course"], description="Retrieve a specific course by ID."
    ),
    create=extend_schema(
        tags=["Course"], description="Create a new course. Only superusers can create."
    ),
    update=extend_schema(
        tags=["Course"], description="Update a course. Only superusers can update."
    ),
    partial_update=extend_schema(
        tags=["Course"],
        description="Partially update a course. Only superusers can update.",
    ),
    destroy=extend_schema(
        tags=["Course"],
        description="Delete or restore a course. Toggles the deleted status.",
    ),
)
class AllCourseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = CourseSerializer

    def get_queryset(self, *args, **kwargs):
        return CourseService.get_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        CourseService.toggle_course_status(instance)
        if instance.is_deleted:
            return Response(
                {"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"message": "Activated successfully"}, status=status.HTTP_200_OK
        )
