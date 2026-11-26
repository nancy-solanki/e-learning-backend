"""
Production settings.
"""

from .base import *

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = False

if not AWS_STORAGE_BUCKET_NAME or not CLOUDFRONT_DOMAIN:
    raise RuntimeError(
        "AWS_STORAGE_BUCKET_NAME and CLOUDFRONT_DOMAIN are required in production."
    )

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS must be configured in production.")


CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")


# ---------------------------------------------------------------------------
# HTTPS / Security
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = True

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))

SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "Lax")

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES["default"]["CONN_MAX_AGE"] = int(os.getenv("DB_CONN_MAX_AGE", "60"))


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

if not EMAIL_HOST:
    raise RuntimeError("EMAIL_HOST must be configured in production.")

if not DEFAULT_FROM_EMAIL:
    raise RuntimeError("DEFAULT_FROM_EMAIL must be configured in production.")


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_ROOT = BASE_DIR / "staticfiles"


# ---------------------------------------------------------------------------
# Cache / Redis
# ---------------------------------------------------------------------------

# Production course catalog search uses the managed OpenSearch endpoint.
OPENSEARCH_ENABLED = True
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "").strip()
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "courses")
OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME", "")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD", "")
OPENSEARCH_USE_SSL = env_bool("OPENSEARCH_USE_SSL", True)
OPENSEARCH_VERIFY_CERTS = env_bool("OPENSEARCH_VERIFY_CERTS", True)

if not OPENSEARCH_URL:
    raise RuntimeError("OPENSEARCH_URL must be configured in production.")

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL must be configured in production.")

CACHES["default"]["LOCATION"] = REDIS_URL

if not os.getenv("CELERY_BROKER_URL"):
    raise RuntimeError("CELERY_BROKER_URL must be configured in production.")


# ---------------------------------------------------------------------------
# Production logging
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": ("{levelname} {asctime} " "{name} {message}"),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
