from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LocalizationViewSet

app_name = "localization"

localization_router = DefaultRouter()
localization_router.register("", LocalizationViewSet, basename="localization")

urlpatterns = [
    path("", include(localization_router.urls)),
]
