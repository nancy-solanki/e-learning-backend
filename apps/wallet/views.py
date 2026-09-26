from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from .serializers import WalletSerializer
from .service import WalletService

# Create your views here.


class IsInstructorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        try:
            return request.user.is_instructor or request.user.is_admin
        except AttributeError:
            return False

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.pk


@extend_schema_view(
    list=extend_schema(
        tags=["Wallet"],
        description="Retrieve the wallet for the authenticated user (instructor).",
    ),
    retrieve=extend_schema(
        tags=["Wallet"], description="Retrieve a specific wallet by ID."
    ),
)
class WalletViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    serializer_class = WalletSerializer
    http_method_names = ["get"]

    def get_queryset(self):
        return WalletService.get_wallet_queryset_by_user(self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        wallet = queryset.first()
        if wallet:
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
        return Response({"detail": "Wallet not found."}, status=404)
