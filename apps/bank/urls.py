from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BankViewSet

app_name = "bank"

router = DefaultRouter()
router.register(r"", BankViewSet, basename="bank")

urlpatterns = [
    path("", include(router.urls)),
]
