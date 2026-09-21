"""
Test settings.
"""

from .base import *

DEBUG = False

SECRET_KEY = "django-test-secret-key-that-is-long-enough-for-jwt"

FRONTEND_URL = "https://example.com/"


ALLOWED_HOSTS = [
    "testserver",
    "localhost",
]


# ---------------------------------------------------------------------------
# Database — in-memory SQLite for fast test execution
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.db"


# ---------------------------------------------------------------------------
# Celery — run tasks synchronously in tests (no broker needed)
# ---------------------------------------------------------------------------

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# ---------------------------------------------------------------------------
# DRF
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [],
}
