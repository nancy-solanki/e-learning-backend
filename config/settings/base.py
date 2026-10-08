"""
Base Django settings.

Shared across development, production, and test environments.
Environment-specific configuration belongs in development.py,
production.py, and test.py.
"""

import os
from datetime import timedelta
from pathlib import Path

import cloudinary
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required.")


DEBUG = env_bool("DEBUG", False)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")

ADMIN_URL = os.getenv("ADMIN_URL", "http://localhost:3000")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3001")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
]

SITE_ID = 1

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "django_filters",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.apple",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_redis",
]


LOCAL_APPS = [
    "apps.core",
    "apps.common",
    "apps.users",
    "apps.category",
    "apps.bank",
    "apps.localization",
    "apps.wallet",
    "apps.course",
    "apps.section",
    "apps.lecture",
    "apps.coupon",
    "apps.enroll",
    "apps.order",
    "apps.transaction",
    "apps.rating",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.core.middleware.UserStatusMiddleware",
]


# ---------------------------------------------------------------------------
# CORS & CSRF
# ---------------------------------------------------------------------------

DEFAULT_DEV_ORIGINS = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:5174,http://127.0.0.1:5174"
)

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", DEFAULT_DEV_ORIGINS)

CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)

CORS_ALLOW_CREDENTIALS = env_bool("CORS_ALLOW_CREDENTIALS", True)

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", DEFAULT_DEV_ORIGINS)


ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "CONN_HEALTH_CHECKS": True,
    }
}


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "MinimumLengthValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "CommonPasswordValidator"),
    },
    {
        "NAME": ("django.contrib.auth.password_validation." "NumericPasswordValidator"),
    },
]


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "users.User"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.auth.cookies.CookieJWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "apps.core.schema.ApplicationSchema",
    "DEFAULT_PAGINATION_CLASS": ("rest_framework.pagination.PageNumberPagination"),
    "PAGE_SIZE": 20,
}


# ---------------------------------------------------------------------------
# OpenAPI / Swagger
# ---------------------------------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": os.getenv("API_TITLE", "Learnify API"),
    "DESCRIPTION": os.getenv(
        "API_DESCRIPTION",
        "E-learning API. Authenticate with a Bearer access token. List "
        "endpoints support documented filters and pagination. Access "
        "remains subject to endpoint roles and ownership; filters never "
        "grant access to other users’ private records.",
    ),
    "VERSION": os.getenv("API_VERSION", "1.0.0"),
    "TAGS": [
        {
            "name": "Authentication",
            "description": "Registration, OAuth/JWT sessions, invitations, and password recovery.",
        },
        {
            "name": "Users",
            "description": "Own profile and administrator-only account management.",
        },
        {
            "name": "Category",
            "description": "Public course categories; administrator-managed multipart uploads.",
        },
        {
            "name": "Course",
            "description": "Public catalog and instructor/admin course management.",
        },
        {
            "name": "Section",
            "description": "Course sections and instructor/admin management.",
        },
        {"name": "Lecture", "description": "Course lectures and content uploads."},
        {
            "name": "Enrollment",
            "description": "Student enrollments and instructor-owned rosters.",
        },
        {"name": "Rating", "description": "Course feedback and instructor replies."},
        {
            "name": "Coupon",
            "description": "Coupon validation and role-scoped management.",
        },
        {"name": "Bank", "description": "Authenticated user's bank accounts."},
        {
            "name": "Wallet",
            "description": "Authenticated instructor/admin's own wallet.",
        },
        {"name": "Order", "description": "Authenticated user's purchases."},
        {
            "name": "Order (Instructor)",
            "description": "Orders assigned to the authenticated instructor.",
        },
        {"name": "Payment", "description": "Payment initiation and verification."},
        {"name": "Transaction", "description": "Authenticated user's ledger entries."},
        {
            "name": "Localization",
            "description": "Languages and countries, managed by administrators.",
        },
        {
            "name": "Admin Dashboard",
            "description": "Administrator-only aggregate metrics.",
        },
    ],
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": ["apps.core.permission.IsSuperuser"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]+",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {"deepLinking": True, "persistAuthorization": False},
    "ENUM_NAME_OVERRIDES": {
        "ContentStatusEnum": "apps.core.schema.content_status_choices",
        "OrderStatusEnum": "apps.core.schema.order_status_choices",
        "TransactionStatusEnum": "apps.core.schema.transaction_status_choices",
        "CourseStatusEnum": "apps.core.schema.course_status_choices",
    },
    "SWAGGER_UI_DIST": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

SIMPLE_JWT = {
    # Token lifetimes – controlled via environment variables
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "15"))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "7"))
    ),
    # Refresh token rotation & blacklisting
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    # Header configuration
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    # User identity fields
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": (
        "rest_framework_simplejwt.authentication.default_user_authentication_rule"
    ),
    # Token classes
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    # JTI (JWT ID) claim used for blacklisting
    "JTI_CLAIM": "jti",
    # Sliding tokens (disabled by default)
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}

REST_AUTH = {
    "USE_JWT": True,
    "SESSION_LOGIN": False,
    "JWT_AUTH_COOKIE": "access_token",
    "JWT_AUTH_REFRESH_COOKIE": "refresh_token",
    "JWT_AUTH_REFRESH_COOKIE_PATH": "/api/v1/auth/",
    "JWT_AUTH_HTTPONLY": True,
    "JWT_AUTH_SECURE": env_bool("AUTH_COOKIE_SECURE", True),
    "JWT_AUTH_SAMESITE": os.getenv("AUTH_COOKIE_SAMESITE", "Lax"),
    "JWT_AUTH_COOKIE_USE_CSRF": True,
}


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.getenv("TIME_ZONE", "UTC")

USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static / Media
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", ""),
    "SECURE": True,
}

# Configure direct SDK uploads as well as django-cloudinary-storage.
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
    api_key=CLOUDINARY_STORAGE["API_KEY"],
    api_secret=CLOUDINARY_STORAGE["API_SECRET"],
    secure=CLOUDINARY_STORAGE["SECURE"],
)

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# ---------------------------------------------------------------------------
# Default primary key
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", False)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")

# Both aliases point to the same env var so either name works in code
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", os.getenv("EMAIL_FROM", ""))
EMAIL_FROM = DEFAULT_FROM_EMAIL  # legacy alias kept for backward compatibility

# Email template directory (used by send_templated_email helper)
EMAIL_TEMPLATE_DIR = "emails"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv(
            "REDIS_URL",
            "redis://127.0.0.1:6379/1",
        ),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}

# Celery uses Redis by default for local development. Deployments should set
# CELERY_BROKER_URL explicitly to the broker available to the worker.
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0"),
)


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# ---------------------------------------------------------------------------
# Security defaults
# ---------------------------------------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "Lax")
