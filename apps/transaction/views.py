from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, generics, mixins
from rest_framework.permissions import IsAuthenticated

from .filters import TransactionFilter
from .models import Transaction
from .serializers import (
    AdminTransactionSerializer,
    TransactionPageSerializer,
    TransactionSerializer,
)
from .service import TransactionService


@extend_schema_view(
    get=extend_schema(
        tags=["Transaction"],
        description=(
            "Retrieve active transactions visible to the caller: admins (superusers "
            "or admin-group members) see all transactions; instructors see "
            "transactions associated with their own active wallet; other "
            "authenticated users see only transactions they own. Admin and "
            "instructor responses include an expanded user summary; other users "
            "receive the base transaction representation. Filter by status, "
            "transaction_type, wallet UUID, exact tx_id, amount_min/max, or "
            "inclusive creation dates (created_at_after/before). Search by "
            "transaction UUID, tx_id, or description. Order by created_at or "
            "amount (prefix with '-' for descending)."
        ),
        responses={200: TransactionPageSerializer},
    ),
)
class TransactionView(mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.none()
    filter_backends = (
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    filterset_class = TransactionFilter
    search_fields = ("id", "tx_id", "description")
    ordering_fields = ("created_at", "amount")
    ordering = ("-created_at",)

    def get_queryset(self):
        if self.request.user.is_admin:
            return TransactionService.get_admin_transactions()
        if self.request.user.is_instructor:
            return TransactionService.get_instructor_transactions(self.request.user)
        return TransactionService.get_user_transactions(self.request.user)

    def get_serializer_class(self):
        if self.request.user.is_admin or self.request.user.is_instructor:
            return AdminTransactionSerializer
        return TransactionSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


@extend_schema_view(
    get=extend_schema(
        tags=["Transaction"],
        description="Retrieve details of a specific transaction by ID.",
    ),
)
class SingleTransactionView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.none()

    def get_queryset(self):
        return TransactionService.get_user_transactions(self.request.user)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
