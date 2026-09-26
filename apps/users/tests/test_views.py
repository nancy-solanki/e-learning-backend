import pytest
from django.contrib.auth.models import Group
from rest_framework import status

from apps.users.tests.factories import UserFactory

# ─────────────────────────────────────────────
# UserProfileView — GET /users/me/
# ─────────────────────────────────────────────


@pytest.mark.django_db
class TestUserProfileView:
    url = "/api/v1/users/me/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_returns_200(self, auth_client, user):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_returns_own_email(self, auth_client, user):
        response = auth_client.get(self.url)
        assert response.data["email"] == user.email

    def test_student_does_not_receive_role(self, auth_client, user):
        student_group, _ = Group.objects.get_or_create(name="student")
        user.groups.add(student_group)

        response = auth_client.get(self.url)

        assert "role" not in response.data

    @pytest.mark.parametrize("role", ["instructor", "admin"])
    def test_instructor_or_admin_receives_role(self, auth_client, user, role):
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        response = auth_client.get(self.url)

        assert response.data["role"] == [role]

    def test_put_updates_first_name(self, auth_client, user):
        response = auth_client.put(self.url, {"first_name": "Updated"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"

    def test_put_updates_phone_number(self, auth_client, user):
        response = auth_client.put(self.url, {"phone_number": "9876543210"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["phone_number"] == "9876543210"


# ─────────────────────────────────────────────
# BecomeInstructorView — POST /users/become-instructor/
# ─────────────────────────────────────────────


@pytest.mark.django_db
class TestBecomeInstructorView:
    url = "/api/v1/users/become-instructor/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.post(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_become_instructor_persists_role(self, auth_client, user):
        response = auth_client.post(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert user.groups.filter(name="instructor").exists()

    def test_already_instructor_returns_400(self, auth_client, user):
        instructor_group, _ = Group.objects.get_or_create(name="instructor")
        user.groups.add(instructor_group)
        response = auth_client.post(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already an instructor" in response.data["message"]


# ─────────────────────────────────────────────
# UserViewSet — /users/ (admin only)
# ─────────────────────────────────────────────


@pytest.mark.django_db
class TestUserViewSet:
    url = "/api/v1/users/"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_admin_user_is_forbidden(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_user_can_list_users(self, admin_client):
        UserFactory.create_batch(3)
        response = admin_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3

    def test_post_not_allowed(self, admin_client):
        response = admin_client.post(self.url, {})
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_delete_not_allowed(self, admin_client, user):
        response = admin_client.delete(f"{self.url}{user.pk}/")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestUserAdminActions:
    def test_admin_toggle_persists(self, admin_client, user):
        url = f"/api/v1/users/{user.pk}/modify_admin_privileges/"
        assert admin_client.put(url).status_code == 200
        user.refresh_from_db()
        assert user.is_admin
        assert admin_client.put(url).status_code == 200
        user.refresh_from_db()
        assert not user.is_admin

    def test_self_admin_toggle_denied(self, admin_client, superuser):
        response = admin_client.put(
            f"/api/v1/users/{superuser.pk}/modify_admin_privileges/"
        )
        assert response.status_code == 400
        assert superuser.groups.filter(name="admin").exists()

    def test_status_toggle_persists(self, admin_client, user):
        url = f"/api/v1/users/{user.pk}/modify_user_status/"
        assert admin_client.put(url).status_code == 200
        user.refresh_from_db()
        assert user.status == "SA"
        assert admin_client.put(url).status_code == 200
        user.refresh_from_db()
        assert user.status == "AC"

    def test_pending_status_returns_400(self, admin_client):
        user = UserFactory(status="PD")
        response = admin_client.put(f"/api/v1/users/{user.pk}/modify_user_status/")
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.status == "PD"

    @pytest.mark.parametrize(
        "action", ["modify_admin_privileges", "modify_user_status"]
    )
    def test_regular_user_cannot_modify(self, auth_client, user, action):
        assert auth_client.put(f"/api/v1/users/{user.pk}/{action}/").status_code == 403

    @pytest.mark.parametrize(
        "action, service",
        [
            ("modify_admin_privileges", "toggle_admin"),
            ("modify_user_status", "toggle_status"),
        ],
    )
    def test_service_failure_returns_500(
        self, admin_client, user, mocker, action, service
    ):
        mocker.patch(
            f"apps.users.views.UserService.{service}",
            side_effect=RuntimeError("Unavailable"),
        )
        response = admin_client.put(f"/api/v1/users/{user.pk}/{action}/")
        assert response.status_code == 500

    def test_instructor_service_failure(self, auth_client, mocker):
        mocker.patch(
            "apps.users.views.UserService.make_instructor",
            side_effect=RuntimeError("Unavailable"),
        )
        assert auth_client.post("/api/v1/users/become-instructor/").status_code == 500

    def test_profile_invalid_update_does_not_persist(self, auth_client, user):
        email = user.email
        response = auth_client.put("/api/v1/users/me/", {"email": "invalid"})
        assert response.status_code == 400
        user.refresh_from_db()
        assert user.email == email

    def test_profile_update_does_not_change_another_user(self, auth_client, user):
        other = UserFactory(first_name="Other")
        response = auth_client.put(
            "/api/v1/users/me/", {"id": str(other.pk), "first_name": "Updated"}
        )
        assert response.status_code == 200
        user.refresh_from_db()
        other.refresh_from_db()
        assert user.first_name == "Updated"
        assert other.first_name == "Other"
