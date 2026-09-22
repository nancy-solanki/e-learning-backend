from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from apps.core.permission import IsSuperuserOrReadOnly

from .models import Category
from .serializers import CategorySerializer
from .service import CategoryService

# Create your views here.

from drf_spectacular.utils import extend_schema_view, extend_schema

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
    lookup_field = 'slug'
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_fields = ('title', 'slug')
    search_fields = ['title', 'slug', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']
    parser_classes = (MultiPartParser, )

    def get_queryset(self):
        return CategoryService.get_queryset_for_user(self.request.user)

    def create(self, request, *args, **kwargs):
        thumbnail = request.FILES.getlist('thumbnail', None)

        try:
            file_instance = CategoryService.upload_thumbnail(thumbnail)
            request.data['thumbnail'] = file_instance.id
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        thumbnail = request.FILES.getlist('thumbnail')

        if not thumbnail and not partial:
            return Response({"detail": "Thumbnail is required."}, status=status.HTTP_400_BAD_REQUEST)
        elif thumbnail:
            try:
                file_instance = CategoryService.upload_thumbnail(thumbnail)
                request.data['thumbnail'] = file_instance.id
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        if category.deleted_at:
            return Response({"detail": "Category already deleted."}, status=status.HTTP_204_NO_CONTENT)
        CategoryService.delete_category(category)
        return Response(status=status.HTTP_204_NO_CONTENT)
