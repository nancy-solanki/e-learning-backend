from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters, generics, serializers, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.permission import IsSuperuser
from apps.core.schema import ErrorSerializer, MessageSerializer
from apps.users.cache import user_profile_cache_key
from apps.users.filters import UserFilter
from apps.users.models import UserNotification
from apps.users.notification_serializers import NotificationSerializer

from .repository import UserRepository
from .schema import UserProfileResponseSerializer, UserResponseSerializer
from .serializers import UserProfileSerializer, UserSerializer
from .services import UserService

User = get_user_model()


class NotificationListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return UserNotification.objects.filter(user=self.request.user).select_related(
            "notification"
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        notification = UserNotification.objects.select_related("notification").filter(
            pk=pk, user=request.user
        ).first()
        if notification is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=("is_read", "read_at", "updated_at"))
        return Response(NotificationSerializer(notification).data)


class AccountStatusChangeSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def to_internal_value(self, data):
        if (
            isinstance(data, dict)
            and "reason" in data
            and not isinstance(data["reason"], str)
        ):
            raise serializers.ValidationError({"reason": "Not a valid string."})
        return super().to_internal_value(data)


@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        description="Retrieve only the authenticated user's profile.",
        responses=UserProfileResponseSerializer,
    ),
    put=extend_schema(
        tags=["Users"],
        description=(
            "Update the authenticated user's profile. All fields are "
            "optional; omitted values are retained."
        ),
        request=UserProfileSerializer(partial=True),
        responses=UserProfileResponseSerializer,
    ),
)
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    throttle_scope = "user_profile"

    def get(self, request):
        cache_key = user_profile_cache_key(request.user.pk)
        profile = cache.get(cache_key)
        if profile is None:
            profile = self.serializer_class(request.user).data
            cache.set(cache_key, profile, settings.USER_PROFILE_CACHE_SECONDS)
        return Response(profile, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        profile = serializer.data
        cache.set(
            user_profile_cache_key(user.pk),
            profile,
            settings.USER_PROFILE_CACHE_SECONDS,
        )
        return Response(profile, status=status.HTTP_200_OK)


@extend_schema_view(
    post=extend_schema(
        tags=["Users"],
        description="Become an instructor as the authenticated user.",
        request=None,
        responses={
            200: MessageSerializer,
            400: MessageSerializer,
            500: ErrorSerializer,
        },
    )
)
class BecomeInstructorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.groups.filter(name="instructor").exists():
            return Response(
                {"message": "User is already an instructor"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            message = UserService.make_instructor(request.user)
            return Response({"message": message}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema_view(
    list=extend_schema(
        tags=["Users"],
        description="List active user records. Administrator access required.",
        responses=UserResponseSerializer(many=True),
    ),
    retrieve=extend_schema(
        tags=["Users"],
        description="Retrieve an account. Administrator access required.",
        responses=UserResponseSerializer,
    ),
    update=extend_schema(
        tags=["Users"],
        description="Update an account. Administrator access required.",
        responses=UserResponseSerializer,
    ),
    destroy=extend_schema(
        tags=["Users"],
        description="Soft-delete an account. Administrators cannot delete themselves.",
    ),
    modify_admin_privileges=extend_schema(
        tags=["Users"],
        description="Toggle another user's admin role. Administrator access required.",
        request=None,
        responses={200: MessageSerializer, 400: ErrorSerializer, 500: ErrorSerializer},
    ),
    modify_instructor_privileges=extend_schema(
        tags=["Users"],
        description="Toggle another user's instructor role. Administrator access required.",
        request=None,
        responses={200: MessageSerializer, 400: ErrorSerializer, 500: ErrorSerializer},
    ),
    modify_user_status=extend_schema(
        tags=["Users"],
        description="Toggle another user's status. Administrator access required.",
        request=AccountStatusChangeSerializer,
        responses={200: MessageSerializer, 400: ErrorSerializer, 500: ErrorSerializer},
    ),
)
class UserViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsSuperuser]
    serializer_class = UserSerializer
    filter_backends = (
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    filterset_class = UserFilter
    search_fields = ("email", "username", "first_name", "last_name")
    ordering_fields = ("created_at", "email", "username")
    ordering = ("-created_at",)
    queryset = UserRepository.get_all_users().filter(deleted_at__isnull=True)
    http_method_names = ["get", "put", "delete"]

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError({"error": "Cannot delete your own account"})
        UserService.delete_user(instance)

    @action(["put"], detail=True)
    def modify_admin_privileges(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response(
                {"error": "Cannot modify your own admin privileges"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            message = UserService.toggle_admin(instance)
            return Response({"message": message}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(["put"], detail=True)
    def modify_instructor_privileges(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance == request.user:
            return Response(
                {"error": "Cannot modify your own instructor privileges"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            message = UserService.toggle_instructor(instance)
            return Response({"message": message}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(["put"], detail=True)
    def modify_user_status(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            return Response(
                {"error": "Cannot suspend your own account"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason_serializer = AccountStatusChangeSerializer(data=request.data)
        reason_serializer.is_valid(raise_exception=True)
        try:
            message = UserService.toggle_status(
                instance, reason=reason_serializer.validated_data.get("reason", "")
            )
            return Response({"message": message}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
