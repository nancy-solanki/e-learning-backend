from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .overview import (
    WalletEntriesView,
    WalletEntryView,
    WalletExportView,
    WalletOverviewView,
)
from .views import WalletViewSet

app_name = "wallet"

router = DefaultRouter()
router.register(r"", WalletViewSet, basename="wallet")

urlpatterns = [
    path("overview/", WalletOverviewView.as_view(), name="overview"),
    path("transactions/", WalletEntriesView.as_view(), name="entries"),
    path("transactions/export/", WalletExportView.as_view(), name="export"),
    path("transactions/<uuid:pk>/", WalletEntryView.as_view(), name="entry"),
    path("", include(router.urls)),
]
