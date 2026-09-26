from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from apps.core.permission import IsSuperuserOrReadOnly

from .serializers import CategorySerializer
from .service import CategoryService


@extend_schema_view(
    list=extend_schema(tags=["Category"]),
    retrieve=extend_schema(tags=["Category"]),
    create=extend_schema(tags=["Category"]),
    update=extend_schema(tags=["Category"]),
    partial_update=extend_schema(tags=["Category"]),
    destroy=extend_schema(tags=["Category"]),
)
class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = (IsSuperuserOrReadOnly,)
    serializer_class = CategorySerializer
    lookup_field = "slug"
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_fields = ("title", "slug")
    search_fields = ["title", "slug", "description"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]
    parser_classes = (MultiPartParser,)

    def get_queryset(self):
        return CategoryService.get_queryset_for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            file_instance = CategoryService.upload_thumbnail(
                request.FILES.getlist("thumbnail")
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user=request.user, thumbnail=file_instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        thumbnail = request.FILES.getlist("thumbnail")
        if not thumbnail and not partial:
            return Response(
                {"detail": "Thumbnail is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        save_kwargs = {}
        if thumbnail:
            try:
                save_kwargs["thumbnail"] = CategoryService.upload_thumbnail(thumbnail)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(**save_kwargs)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        CategoryService.delete_category(category)
        return Response(status=status.HTTP_204_NO_CONTENT)
