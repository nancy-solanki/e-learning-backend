from allauth.socialaccount.providers.apple.client import AppleOAuth2Client
from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.app_settings import api_settings as auth_settings
from dj_rest_auth.jwt_auth import set_jwt_cookies, unset_jwt_cookies
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.schema import MessageSerializer

from .cookies import CsrfProtectedMixin, validate_session_user
from .schema import CsrfTokenSerializer
from .serializers import (
    SendPasswordResetEmailSerializer,
    SocialLoginSerializer,
    StaffSignInSerializer,
    UserActivateAccountSerializer,
    UserChangePasswordSerializer,
    UserPasswordResetSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


@extend_schema_view(get=extend_schema(responses={200: CsrfTokenSerializer}))
class CsrfTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        response = Response({"csrfToken": get_token(request)})
        response["Cache-Control"] = "no-store"
        return response


@extend_schema_view(post=extend_schema(responses={200: MessageSerializer}))
class CookieSignInView(CsrfProtectedMixin, TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = RefreshToken(response.data["refresh"])
        user = User.objects.get(pk=token["user_id"])
        validate_session_user(user, token)
        set_jwt_cookies(response, response.data["access"], response.data["refresh"])
        response.data = {"message": "Signed in successfully"}
        response["Cache-Control"] = "no-store"
        return response


@extend_schema_view(
    post=extend_schema(request=None, responses={200: MessageSerializer})
)
class CookieRefreshView(CsrfProtectedMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'

    def post(self, request):
        raw_token = request.COOKIES.get(auth_settings.JWT_AUTH_REFRESH_COOKIE)
        if not raw_token:
            raise InvalidToken("Refresh cookie is missing.")
        try:
            token = RefreshToken(raw_token)
            user = User.objects.filter(pk=token["user_id"], is_active=True).first()
            if user is None:
                raise InvalidToken("User is not active.")
            validate_session_user(user, token)
            serializer = TokenRefreshSerializer(data={"refresh": raw_token})
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise InvalidToken(str(exc)) from exc
        response = Response({"message": "Session refreshed"})
        set_jwt_cookies(
            response,
            serializer.validated_data["access"],
            serializer.validated_data["refresh"],
        )
        response["Cache-Control"] = "no-store"
        return response


class CookieSocialLoginView(CsrfProtectedMixin, SocialLoginView):
    authentication_classes = []

    def get_response(self):
        response = super().get_response()
        response.data = {"message": "Signed in successfully"}
        response["Cache-Control"] = "no-store"
        return response


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Sign in with an account belonging exclusively to admin/instructor groups.",
        request=StaffSignInSerializer,
        responses={200: MessageSerializer},
    )
)
class StaffSignInView(CookieSignInView):
    serializer_class = StaffSignInSerializer


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Exchange Google OAuth credentials for application tokens.",
        request=SocialLoginSerializer,
        responses={200: MessageSerializer},
    )
)
class GoogleLoginView(CookieSocialLoginView):
    permission_classes = [AllowAny]
    serializer_class = SocialLoginSerializer
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


@extend_schema_view(
    post=extend_schema(
        tags=["Authentication"],
        description="Exchange Apple OAuth credentials for application tokens.",
        request=SocialLoginSerializer,
        responses={200: MessageSerializer},
    )
)
class AppleLoginView(CookieSocialLoginView):
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
        description="Blacklist the refresh cookie and clear authentication cookies.",
        request=None,
        responses={204: None},
    )
)
class UserLogoutView(CsrfProtectedMixin, APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        raw_token = request.COOKIES.get(auth_settings.JWT_AUTH_REFRESH_COOKIE)
        if raw_token:
            try:
                RefreshToken(raw_token).blacklist()
            except TokenError:
                pass  # Always clear expired or already revoked cookies.
        response = Response(status=status.HTTP_204_NO_CONTENT)
        unset_jwt_cookies(response)
        response["Cache-Control"] = "no-store"
        return response


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
