"""
Development settings.
"""

from .base import *

DEBUG = True

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1",
)


# ---------------------------------------------------------------------------
# Development database
# ---------------------------------------------------------------------------

# Uses PostgreSQL from base.py.
# Override DB_* in .env if necessary.


# ---------------------------------------------------------------------------
# Development email
# ---------------------------------------------------------------------------

# Use the configured backend when SMTP settings are provided; otherwise keep
# development email local and visible in the console.
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

# Email tasks run through Celery in the background during development.
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = env_bool("CELERY_TASK_EAGER_PROPAGATES", False)


# ---------------------------------------------------------------------------
# Development cache
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "development-cache",
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"


# ---------------------------------------------------------------------------
# Development security
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# ---------------------------------------------------------------------------
# DRF
# ---------------------------------------------------------------------------

REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] = ("rest_framework.permissions.AllowAny",)
