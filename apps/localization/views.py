from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.permission import IsSuperuserOrReadOnly
from apps.core.schema import MessageSerializer

from .filters import LocalizationFilter
from .models import Localization
from .pagination import LocalizationPagination
from .serializers import LocalizationSerializer
from .service import LocalizationService


@extend_schema_view(
    list=extend_schema(
        tags=["Localization"],
        description=(
            "List all localizations. Superusers and admins see all, other authenticated users "
            "see only active ones."
        ),
    ),
    retrieve=extend_schema(
        tags=["Localization"], description="Retrieve a specific localization by ID."
    ),
    create=extend_schema(
        tags=["Localization"],
        description="Create a new localization. Only superusers and admins can create.",
    ),
    update=extend_schema(
        tags=["Localization"],
        description="Update a localization. Only superusers and admins can update.",
    ),
    partial_update=extend_schema(
        tags=["Localization"],
        description="Partially update a localization. Only superusers and admins can update.",
    ),
    destroy=extend_schema(
        responses={200: MessageSerializer, 204: None},
        tags=["Localization"],
        description="Delete or restore a localization. Toggles the deleted status.",
    ),
)
class LocalizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperuserOrReadOnly, IsAuthenticated]
    serializer_class = LocalizationSerializer
    queryset = Localization.objects.none()
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = LocalizationFilter
    pagination_class = LocalizationPagination
    search_fields = ("language_name", "country")
    ordering_fields = ("language_name", "country", "created_at", "updated_at")
    ordering = ("-created_at", "-id")

    def get_queryset(self, *args, **kwargs):
        return LocalizationService.get_queryset_for_user(self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        LocalizationService.toggle_localization_status(instance)
        if instance.is_deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {"message": "Activated successfully"}, status=status.HTTP_200_OK
        )
