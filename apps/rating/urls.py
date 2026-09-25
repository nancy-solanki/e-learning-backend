from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RatingByInstructorView, RatingViewSet

app_name = "rating"

router = DefaultRouter()
router.register(r"management", RatingViewSet, basename="rating-management")

urlpatterns = [
    path("", include(router.urls)),
    path("instructor/", RatingByInstructorView.as_view(), name="rating-by-instructor"),
]
