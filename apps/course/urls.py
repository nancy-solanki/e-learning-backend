from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminCourseListView,
    AllCourseViewSet,
    CourseByCategoryView,
    CourseViewSet,
)

app_name = "course"

courseRouter = DefaultRouter()
courseRouter.register("", CourseViewSet, basename="Course")

allCourseRouter = DefaultRouter()
allCourseRouter.register("", AllCourseViewSet, basename="Course")

urlpatterns = [
    path("admin/all/", AdminCourseListView.as_view(), name="admin-course-list"),
    path("instructor/all/", include(allCourseRouter.urls)),
    path("", include(courseRouter.urls)),
    path("category/<slug>/", CourseByCategoryView.as_view()),
    # path('enroll/my-courses/', CourseByEnrollView.as_view()),  # TODO: Implement enroll app
]
