from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import EnrollByCourseView, EnrollViewSet

app_name = "enroll"

router = DefaultRouter()
router.register(r"management", EnrollViewSet, basename="enroll-management")

urlpatterns = [
    path("", include(router.urls)),
    path("course/<slug:slug>/", EnrollByCourseView.as_view(), name="enroll-by-course"),
]
