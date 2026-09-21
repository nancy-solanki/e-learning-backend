from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.auth.urls", namespace="auth")),
    path("users/", include("apps.users.urls", namespace="user")),
]
