from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import serializers


class CsrfTokenSerializer(serializers.Serializer):
    csrfToken = serializers.CharField(read_only=True)


class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "apps.auth.cookies.CookieJWTAuthentication"
    name = "cookieJWT"

    def get_security_definition(self, auto_schema):
        from dj_rest_auth.app_settings import api_settings

        return {
            "type": "apiKey",
            "in": "cookie",
            "name": api_settings.JWT_AUTH_COOKIE,
            "description": "HttpOnly JWT cookie; mutations also require X-CSRFToken.",
        }
