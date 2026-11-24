from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .invitations import InviteUserView, ResendInvitationView
from .views import (
    BecomeInstructorView,
    NotificationListView,
    NotificationReadView,
    UserProfileView,
    UserViewSet,
)

app_name = "user"

router = DefaultRouter()
router.register("", UserViewSet)

urlpatterns = [
    path("invite/", InviteUserView.as_view(), name="invite"),
    path(
        "<uuid:pk>/resend-invite/", ResendInvitationView.as_view(), name="resend-invite"
    ),
    path("me/", UserProfileView.as_view(), name="profile"),
    path("me/notifications/", NotificationListView.as_view(), name="notifications"),
    path(
        "me/notifications/<uuid:pk>/read/",
        NotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "become-instructor/", BecomeInstructorView.as_view(), name="become-instructor"
    ),
    path("", include(router.urls), name="user"),
]
