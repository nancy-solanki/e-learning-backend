from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet

app_name = "category"

category_router = DefaultRouter()
category_router.register("", CategoryViewSet, basename="category")

urlpatterns = [
    path("", include(category_router.urls)),
]
