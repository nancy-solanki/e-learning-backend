from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.email_notifications import queue_notification_email
from apps.core.permission import IsInstructorOrReadOnly
from apps.core.schema import MessageSerializer

from .filters import BankFilter
from .models import Bank
from .repository import BankRepository
from .serializers import BankSerializer
from .service import BankService


@extend_schema_view(
    list=extend_schema(
        tags=["Bank"],
        description="Retrieve a list of all bank accounts associated with the authenticated user.",
    ),
    retrieve=extend_schema(
        tags=["Bank"],
        description="Retrieve details of a specific bank account by its ID.",
    ),
    create=extend_schema(
        tags=["Bank"],
        description=(
            "Add a new bank account. The first added account is automatically set as default."
        ),
    ),
    update=extend_schema(
        request=BankSerializer(partial=True),
        responses={
            200: PolymorphicProxySerializer(
                component_name="BankUpdateResponse",
                serializers=[BankSerializer, MessageSerializer],
                resource_type_field_name=None,
            )
        },
        tags=["Bank"],
        description=(
            "Update bank account details. Use this to set an account as default by "
            'sending `{"default": true}`.'
        ),
    ),
    partial_update=extend_schema(
        responses={
            200: PolymorphicProxySerializer(
                component_name="BankUpdateResponse",
                serializers=[BankSerializer, MessageSerializer],
                resource_type_field_name=None,
            )
        },
        tags=["Bank"],
        description="Partially update bank account details.",
    ),
    destroy=extend_schema(
        tags=["Bank"],
        description="Toggle deletion status of a bank account. Primary accounts cannot be deleted.",
    ),
)
class BankViewSet(viewsets.ModelViewSet):
    permission_classes = [IsInstructorOrReadOnly, IsAuthenticated]
    serializer_class = BankSerializer
    queryset = Bank.objects.none()
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = BankFilter
    search_fields = ("name", "account_number", "ifsc_code")
    ordering_fields = ("created_at", "name")
    ordering = ("-created_at",)

    def get_queryset(self):
        return BankRepository.get_banks_by_user(self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.data.get("default"):
            message = BankService.set_default_bank(request.user, instance.id)
            queue_notification_email(
                request.user,
                subject="Your default payout account changed",
                title="Default payout account changed",
                message=(
                    "Your default payout account ending in "
                    f"{instance.account_number[-4:]} was changed."
                ),
                preference_required=False,
            )
            return Response({"message": message}, status=status.HTTP_200_OK)
        else:
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            changed = any(
                getattr(instance, field) != value
                for field, value in serializer.validated_data.items()
            )
            serializer.save()
            if changed:
                queue_notification_email(
                    request.user,
                    subject="Your payout bank details changed",
                    title="Payout bank details changed",
                    message=(
                        "The bank details on your Learnify account were changed. "
                        "Contact support immediately if you did not make this change."
                    ),
                    preference_required=False,
                )
            return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        was_deleted = instance.is_deleted
        message = BankService.toggle_delete_bank(instance)
        if was_deleted != instance.is_deleted:
            queue_notification_email(
                request.user,
                subject="Your payout bank account changed",
                title="Payout bank account updated",
                message=(
                    f"Your payout account ending in {instance.account_number[-4:]} "
                    f"was {'restored' if was_deleted else 'removed'}."
                ),
                preference_required=False,
            )

        status_code = status.HTTP_200_OK
        if "Deleted" in message:
            status_code = status.HTTP_204_NO_CONTENT

        return Response({"message": message}, status=status_code)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        bank = serializer.instance
        queue_notification_email(
            self.request.user,
            subject="A payout bank account was added",
            title="Payout bank account added",
            message=(
                f"A payout account ending in {bank.account_number[-4:]} was added "
                "to your Learnify account."
            ),
            preference_required=False,
        )
