from django.urls import path

from .views import AdminDashboardChartsView, AdminDashboardStatsView

urlpatterns = [
    path("stats/", AdminDashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("charts/", AdminDashboardChartsView.as_view(), name="admin-dashboard-charts"),
]
