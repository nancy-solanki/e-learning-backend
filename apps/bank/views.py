from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import BankSerializer
from .repository import BankRepository
from .service import BankService
from .filters import BankFilter
from apps.core.permission import IsInstructorOrReadOnly
from drf_spectacular.utils import extend_schema, extend_schema_view


@extend_schema_view(
    list=extend_schema(
        tags=["Bank"],
        description="Retrieve a list of all bank accounts associated with the authenticated user."
    ),
    retrieve=extend_schema(
        tags=["Bank"],
        description="Retrieve details of a specific bank account by its ID."
    ),
    create=extend_schema(
        tags=["Bank"],
        description="Add a new bank account. The first added account is automatically set as default."
    ),
    update=extend_schema(
        tags=["Bank"],
        description="Update bank account details. Use this to set an account as default by sending `{\"default\": true}`."
    ),
    partial_update=extend_schema(
        tags=["Bank"],
        description="Partially update bank account details."
    ),
    destroy=extend_schema(
        tags=["Bank"],
        description="Toggle deletion status of a bank account. Primary accounts cannot be deleted."
    ),
)
class BankViewSet(viewsets.ModelViewSet):
    permission_classes = [IsInstructorOrReadOnly, IsAuthenticated]
    serializer_class = BankSerializer
    filter_backends = (DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter)
    filterset_class = BankFilter
    search_fields = ('name', 'account_number', 'ifsc_code')
    ordering_fields = ('created_at', 'name')
    ordering = ('-created_at',)

    def get_queryset(self):
        return BankRepository.get_banks_by_user(self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.data.get("default"):
            message = BankService.set_default_bank(request.user, instance.id)
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        message = BankService.toggle_delete_bank(instance)
        
        status_code = status.HTTP_200_OK
        if "Deleted" in message:
            status_code = status.HTTP_204_NO_CONTENT
            
        return Response({"message": message}, status=status_code)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)