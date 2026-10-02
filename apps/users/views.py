from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.permission import IsSuperuser
from apps.users.filters import UserFilter

from .repository import UserRepository
from .serializers import UserProfileSerializer, UserSerializer
from .services import UserService

User = get_user_model()


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get(self, request):
        return Response(
            self.serializer_class(request.user).data, status=status.HTTP_200_OK
        )

    def put(self, request):
        user = request.user
        serializer = self.serializer_class(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({**serializer.data}, status=status.HTTP_200_OK)


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
    def modify_user_status(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            return Response(
                {"error": "Cannot suspend your own account"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            message = UserService.toggle_status(instance)
            return Response({"message": message}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
