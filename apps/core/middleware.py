import jwt
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)

class UserStatusMiddleware:
    """
    Middleware to validate JWT tokens and check user status (Pending, Suspended)
    and password validity (iat vs password_changed_at).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', "")
        token = None
        
        if auth_header.startswith('Bearer '):
            parts = auth_header.split(' ')
            if len(parts) == 2:
                token = parts[1]

        if token:
            try:
                # Decodes token using the project's SECRET_KEY
                # We verify the signature to ensure security
                payload = jwt.decode(
                    token, 
                    key=settings.SECRET_KEY, 
                    algorithms=["HS256"],
                    options={"verify_signature": True} 
                )

                # SimpleJWT uses 'id' as specified in settings.py
                user_id = payload.get("id")
                iat = payload.get("iat")

                if not user_id:
                    raise jwt.InvalidTokenError("user_id not found in token")

                user = User.objects.filter(id=user_id).first()
                if not user:
                    raise jwt.InvalidTokenError("User not found")

                # Check account status
                if user.status == User.Status.PENDING:
                    return self._build_error_response(
                        _("Email is not verified. Please check your email inbox."),
                        status.HTTP_403_FORBIDDEN
                    )
                
                if user.status == User.Status.SUSPEND:
                    return self._build_error_response(
                        _("Account is not active"),
                        status.HTTP_403_FORBIDDEN
                    )

                # Check if password was changed after token was issued
                if user.password_changed_at:
                    password_changed_timestamp = user.password_changed_at.timestamp()
                    if iat < password_changed_timestamp:
                        return self._build_error_response(
                            _("Credentials are Invalid"),
                            status.HTTP_401_UNAUTHORIZED
                        )

                # Set request.user for downstream use
                request.user = user

            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception) as e:
                logger.warning(f"JWT Middleware error: {str(e)}")
                return self._build_invalid_token_response()

        return self.get_response(request)

    def _build_error_response(self, message, status_code):
        response = Response({
            "errors": {"non_field_error": [message]}
        }, status=status_code)
        return self._render_drf_response(response)

    def _build_invalid_token_response(self):
        response = Response({
            "errors": {
                "detail": "Given token not valid for any token type",
                "code": "token_not_valid",
                "messages": [
                    {
                        "token_class": "AccessToken",
                        "token_type": "access",
                        "message": "Token is not valid or expired"
                    }
                ]
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
        return self._render_drf_response(response)

    def _render_drf_response(self, response):
        """
        Manually renders a DRF Response object into a standard Django HttpResponse.
        """
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}
        response.render()
        return response
