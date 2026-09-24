from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AllSectionViewSet, SectionByCourseView, SectionViewSet

app_name = "section"

sectionRouter = DefaultRouter()
sectionRouter.register("", SectionViewSet, basename="Section")

allSectionRouter = DefaultRouter()
allSectionRouter.register("", AllSectionViewSet, basename="Section")

urlpatterns = [
    path("instructor/all/", include(allSectionRouter.urls)),
    path("", include(sectionRouter.urls)),
    path("course/<slug>/", SectionByCourseView.as_view()),
]
