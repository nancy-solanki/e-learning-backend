from allauth.socialaccount.providers.apple.client import AppleOAuth2Client
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.serializers import JWTSerializer
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.schema import MessageSerializer

from .schema import TokenPairSerializer
from .serializers import (
    SendPasswordResetEmailSerializer,
    SocialLoginSerializer,
    StaffSignInSerializer,
    UserActivateAccountSerializer,
    UserChangePasswordSerializer,
    UserLogoutSerializer,
    UserPasswordResetSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Sign in with an account belonging exclusively to admin/instructor groups.",
        request=StaffSignInSerializer,
        responses={200: TokenPairSerializer},
    )
)
class StaffSignInView(TokenObtainPairView):
    serializer_class = StaffSignInSerializer


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Exchange Google OAuth credentials for application tokens.",
        request=SocialLoginSerializer,
        responses={200: JWTSerializer},
    )
)
class GoogleLoginView(SocialLoginView):
    permission_classes = [AllowAny]
    serializer_class = SocialLoginSerializer
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Exchange Apple OAuth credentials for application tokens.",
        request=SocialLoginSerializer,
        responses={200: JWTSerializer},
    )
)
class AppleLoginView(SocialLoginView):
    permission_classes = [AllowAny]
    serializer_class = SocialLoginSerializer
    adapter_class = AppleOAuth2Adapter
    client_class = AppleOAuth2Client


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Register a student and send an account activation email.",
        request=UserRegistrationSerializer,
        responses={201: MessageSerializer},
    )
)
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


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Activate an account using its emailed UID and token.",
        request=None,
        responses={200: MessageSerializer},
    )
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


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Blacklist the supplied refresh token. The response has no body.",
        request=UserLogoutSerializer,
        responses={204: None},
    )
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


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Change the authenticated user’s password.",
        request=UserChangePasswordSerializer,
        responses={200: MessageSerializer},
    )
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


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Send a password reset email for an active account.",
        request=SendPasswordResetEmailSerializer,
        responses={200: MessageSerializer},
    )
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


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Reset a password using its emailed UID and token.",
        request=UserPasswordResetSerializer,
        responses={200: MessageSerializer},
    )
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
