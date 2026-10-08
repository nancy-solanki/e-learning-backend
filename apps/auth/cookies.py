"""Cookie JWT authentication and CSRF enforcement for browser sessions."""

from dj_rest_auth.jwt_auth import JWTCookieAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied


class CookieJWTAuthentication(JWTCookieAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        validate_session_user(user, validated_token)
        return user


def validate_session_user(user, token):
    if user.status != user.Status.ACTIVE:
        raise PermissionDenied("Account is not active or email is not verified.")
    if user.password_changed_at and token["iat"] < int(
        user.password_changed_at.timestamp()
    ):
        raise AuthenticationFailed("Credentials are invalid. Please sign in again.")


class CsrfProtectedMixin:
    """Enforce CSRF even on anonymous login/refresh/logout requests."""

    def initial(self, request, *args, **kwargs):
        JWTCookieAuthentication().enforce_csrf(request)
        super().initial(request, *args, **kwargs)
