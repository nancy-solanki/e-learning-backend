import pytest
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.tests.factories import SuperuserFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def superuser(db):
    admin_group, _ = Group.objects.get_or_create(name="admin")
    su = SuperuserFactory()
    su.groups.add(admin_group)
    return su


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, superuser):
    api_client.force_authenticate(user=superuser)
    return api_client


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

    def test_authenticated_non_instructor_returns_500_until_model_method_added(
        self, auth_client, user
    ):
        """
        Expects 500 because become_instructor() is not yet implemented
        on the User model. Update to 200 once the model method is added.
        """
        response = auth_client.post(self.url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

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
