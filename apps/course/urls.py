from django.urls import path, include
from .views import CourseByCategoryView, AllCourseViewSet, CourseViewSet
from rest_framework.routers import DefaultRouter

app_name = "course"

courseRouter = DefaultRouter()
courseRouter.register('', CourseViewSet, basename='Course')

allCourseRouter = DefaultRouter()
allCourseRouter.register('', AllCourseViewSet, basename='Course')

urlpatterns = [
    path('instructor/all/', include(allCourseRouter.urls)),
    path('', include(courseRouter.urls)),
    path('category/<slug>/', CourseByCategoryView.as_view()),
    # path('enroll/my-courses/', CourseByEnrollView.as_view()),  # TODO: Implement enroll app
]
