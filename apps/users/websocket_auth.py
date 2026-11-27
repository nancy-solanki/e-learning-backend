from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _user_from_token(raw_token):
    try:
        token = AccessToken(raw_token)
        user = get_user_model().objects.get(pk=token["user_id"])
    except Exception:
        return AnonymousUser()
    if (
        not user.is_active
        or user.deleted_at is not None
        or user.status != user.Status.ACTIVE
        or (
            user.password_changed_at
            and token["iat"] < int(user.password_changed_at.timestamp())
        )
    ):
        return AnonymousUser()
    return user


class CookieJWTAuthMiddleware:
    """Authenticate websocket connections using the same access cookie as REST."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        cookies = {}
        for item in headers.get(b"cookie", b"").decode().split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                cookies[key] = value
        cookie_name = settings.REST_AUTH.get("JWT_AUTH_COOKIE", "access_token")
        token = cookies.get(cookie_name)
        if token:
            scope["user"] = await _user_from_token(token)
        return await self.inner(scope, receive, send)


def CookieJWTAuthMiddlewareStack(inner):
    from channels.auth import AuthMiddlewareStack

    # AuthMiddlewareStack initializes scope["user"] from Django sessions.
    # Apply JWT-cookie auth after it so the access token is not overwritten.
    return AuthMiddlewareStack(CookieJWTAuthMiddleware(inner))
