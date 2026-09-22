from django.urls import path
from .views import AdminDashboardStatsView, AdminDashboardChartsView

urlpatterns = [
    path('stats/', AdminDashboardStatsView.as_view(), name='admin-dashboard-stats'),
    path('charts/', AdminDashboardChartsView.as_view(), name='admin-dashboard-charts'),
]
