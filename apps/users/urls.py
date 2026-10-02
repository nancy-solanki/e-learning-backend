from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .invitations import InviteUserView, ResendInvitationView
from .views import BecomeInstructorView, UserProfileView, UserViewSet

app_name = "user"

router = DefaultRouter()
router.register("", UserViewSet)

urlpatterns = [
    path("invite/", InviteUserView.as_view(), name="invite"),
    path(
        "<uuid:pk>/resend-invite/", ResendInvitationView.as_view(), name="resend-invite"
    ),
    path("me/", UserProfileView.as_view(), name="profile"),
    path(
        "become-instructor/", BecomeInstructorView.as_view(), name="become-instructor"
    ),
    path("", include(router.urls), name="user"),
]
