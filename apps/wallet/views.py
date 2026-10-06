from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_serializer,
    extend_schema_view,
)
from rest_framework import filters, viewsets
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.core.schema import DetailSerializer

from .filters import WalletFilter
from .models import Wallet
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


@extend_schema_serializer(many=False)
class WalletResponseSerializer(WalletSerializer):
    """The collection URL returns one wallet, not a paginated list."""


@extend_schema_view(
    list=extend_schema(
        tags=["Wallet"],
        responses={200: WalletResponseSerializer, 404: DetailSerializer},
        description=(
            "Retrieve the authenticated user's wallet, optionally filtered by "
            "wallet type, earnings, withdrawals, or creation date. Search by wallet "
            "ID or owner username, name, or email. Returns 404 when no wallet matches."
        ),
    ),
    retrieve=extend_schema(
        tags=["Wallet"], description="Retrieve a specific wallet by ID."
    ),
)
class WalletViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    pagination_class = None
    serializer_class = WalletSerializer
    queryset = Wallet.objects.none()
    http_method_names = ["get"]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = WalletFilter
    search_fields = (
        "id",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )

    def get_queryset(self):
        return WalletService.get_wallet_queryset_by_user(self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        wallet = queryset.first()
        if wallet:
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
        return Response({"detail": "Wallet not found."}, status=404)
