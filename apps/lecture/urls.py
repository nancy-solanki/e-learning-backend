from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AllLectureViewSet, LectureBySectionView, LectureViewSet

app_name = "lecture"

lectureRouter = DefaultRouter()
lectureRouter.register("", LectureViewSet, basename="Lecture")

allLectureRouter = DefaultRouter()
allLectureRouter.register("", AllLectureViewSet, basename="Lecture")

urlpatterns = [
    path("instructor/all/", include(allLectureRouter.urls)),
    path("", include(lectureRouter.urls)),
    path("section/<slug>/", LectureBySectionView.as_view()),
]
