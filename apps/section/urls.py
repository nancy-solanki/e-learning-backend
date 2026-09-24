from django.urls import path, include
from .views import SectionByCourseView, AllSectionViewSet, SectionViewSet
from rest_framework.routers import DefaultRouter

app_name = "section"

sectionRouter = DefaultRouter()
sectionRouter.register('', SectionViewSet, basename='Section')

allSectionRouter = DefaultRouter()
allSectionRouter.register('', AllSectionViewSet, basename='Section')

urlpatterns = [
    path('instructor/all/', include(allSectionRouter.urls)),
    path('', include(sectionRouter.urls)),
    path('course/<slug>/', SectionByCourseView.as_view()),
]
