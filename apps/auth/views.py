from allauth.socialaccount.providers.apple.client import AppleOAuth2Client
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    SendPasswordResetEmailSerializer,
    SocialLoginSerializer,
    UserActivateAccountSerializer,
    UserChangePasswordSerializer,
    UserLogoutSerializer,
    UserPasswordResetSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


class GoogleLoginView(SocialLoginView):
    permission_classes = [AllowAny]
    serializer_class = SocialLoginSerializer
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


class AppleLoginView(SocialLoginView):
    permission_classes = [AllowAny]
    serializer_class = SocialLoginSerializer
    adapter_class = AppleOAuth2Adapter
    client_class = AppleOAuth2Client


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Email verify link send to your email. Please check your email inbox."
            },
            status=status.HTTP_201_CREATED,
        )


class UserActivateAccountView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = UserActivateAccountSerializer(
            data=request.data, context={"uid": uid, "token": token}
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "Account activated successfully"}, status=status.HTTP_200_OK
        )


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserLogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Signed out successfully"}, status=status.HTTP_204_NO_CONTENT
        )


class UserChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserChangePasswordSerializer(
            data=request.data, context={"user": request.user}
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "Password changed successfully"}, status=status.HTTP_200_OK
        )


class SendPasswordResetEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendPasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "message": "Password reset link send to your email. Please check your email inbox."
            },
            status=status.HTTP_200_OK,
        )


class UserPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = UserPasswordResetSerializer(
            data=request.data, context={"uid": uid, "token": token}
        )
        serializer.is_valid(raise_exception=True)
        return Response(
            {"message": "Password reset successfully"}, status=status.HTTP_200_OK
        )
