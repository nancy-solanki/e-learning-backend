from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.core.permission import IsSuperuser

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
    queryset = UserRepository.get_all_users()
    http_method_names = ["get", "put"]

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
        try:
            message = UserService.toggle_status(instance)
            return Response({"message": message}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
