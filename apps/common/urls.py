from django.urls import path

from .views import (
    AdminDashboardChartsView,
    AdminDashboardStatsView,
    AdminDashboardView,
    InstructorDashboardView,
)

urlpatterns = [
    path("admin/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("stats/", AdminDashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("charts/", AdminDashboardChartsView.as_view(), name="admin-dashboard-charts"),
    path("instructor/", InstructorDashboardView.as_view(), name="instructor-dashboard"),
]
