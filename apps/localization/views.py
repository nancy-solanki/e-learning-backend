from rest_framework.response import Response
from rest_framework import status
from .serializers import LocalizationSerializer
from .service import LocalizationService
from apps.core.permission import IsSuperuserOrReadOnly
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from drf_spectacular.utils import extend_schema_view, extend_schema


@extend_schema_view(
    list=extend_schema(
        tags=["Localization"],
        description="List all localizations. Superusers see all, other authenticated users see only active ones."
    ),
    retrieve=extend_schema(
        tags=["Localization"],
        description="Retrieve a specific localization by ID."
    ),
    create=extend_schema(
        tags=["Localization"],
        description="Create a new localization. Only superusers can create."
    ),
    update=extend_schema(
        tags=["Localization"],
        description="Update a localization. Only superusers can update."
    ),
    partial_update=extend_schema(
        tags=["Localization"],
        description="Partially update a localization. Only superusers can update."
    ),
    destroy=extend_schema(
        tags=["Localization"],
        description="Delete or restore a localization. Toggles the deleted status."
    ),
)
class LocalizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsSuperuserOrReadOnly, IsAuthenticated]
    serializer_class = LocalizationSerializer

    def get_queryset(self, *args, **kwargs):
        return LocalizationService.get_queryset_for_user(self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        LocalizationService.toggle_localization_status(instance)
        if instance.is_deleted:
            return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "Activated successfully"}, status=status.HTTP_200_OK)
