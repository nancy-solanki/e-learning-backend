from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, mixins
from rest_framework.permissions import IsAuthenticated

from .serializers import TransactionSerializer
from .service import TransactionService


@extend_schema_view(
    get=extend_schema(
        tags=["Transaction"],
        description="Retrieve a list of transactions for the authenticated user.",
    ),
)
class TransactionView(mixins.ListModelMixin, generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return TransactionService.get_user_transactions(self.request.user)

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

    def get_queryset(self):
        return TransactionService.get_transaction_queryset()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
