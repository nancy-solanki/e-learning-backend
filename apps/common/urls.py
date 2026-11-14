from django.urls import path

from .views import (
    AdminDashboardChartsView,
    AdminDashboardStatsView,
    InstructorDashboardView,
)

urlpatterns = [
    path("stats/", AdminDashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("charts/", AdminDashboardChartsView.as_view(), name="admin-dashboard-charts"),
    path("instructor/", InstructorDashboardView.as_view(), name="instructor-dashboard"),
]
