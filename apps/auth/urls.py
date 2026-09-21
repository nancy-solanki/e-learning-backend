from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.auth.views import (
    AppleLoginView,
    GoogleLoginView,
    SendPasswordResetEmailView,
    UserActivateAccountView,
    UserChangePasswordView,
    UserLogoutView,
    UserPasswordResetView,
    UserRegistrationView,
)

app_name = "auth"

urlpatterns = [
    path("sign-up/", UserRegistrationView.as_view(), name="sign-up"),
    path("sign-in/", TokenObtainPairView.as_view(), name="sign-in"),
    path("sign-out/", UserLogoutView.as_view(), name="sign-out"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("apple/", AppleLoginView.as_view(), name="apple-login"),
    path("change-password/", UserChangePasswordView.as_view(), name="change-password"),
    path(
        "send-reset-password-email/",
        SendPasswordResetEmailView.as_view(),
        name="send-reset-password-email",
    ),
    path(
        "reset-password/<uid>/<token>/",
        UserPasswordResetView.as_view(),
        name="reset-password",
    ),
    path(
        "activate-account/<uid>/<token>/",
        UserActivateAccountView.as_view(),
        name="activate-account",
    ),
]
