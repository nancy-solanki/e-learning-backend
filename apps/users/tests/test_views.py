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

    def test_student_receives_role(self, auth_client, user):
        student_group, _ = Group.objects.get_or_create(name="student")
        user.groups.add(student_group)

        response = auth_client.get(self.url)

        assert response.data["role"] == ["student"]

    @pytest.mark.parametrize("role", ["instructor", "admin"])
    def test_instructor_or_admin_receives_role(self, auth_client, user, role):
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        response = auth_client.get(self.url)

        assert response.data["role"] == [role]

    def test_put_updates_full_name(self, auth_client, user):
        response = auth_client.put(self.url, {"full_name": "Updated"})
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Updated"

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

    def test_delete_soft_deletes_and_hides_user(self, admin_client, user):
        from apps.course.tests.factories import CourseFactory

        course = CourseFactory(instructor=user)
        target = f"{self.url}{user.pk}/"
        response = admin_client.delete(target)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.content
        user.refresh_from_db()
        assert user.deleted_at is not None
        assert not user.is_active
        assert user.status == user.Status.INACTIVE
        course.refresh_from_db()
        assert course.instructor_id == user.pk
        assert admin_client.get(target).status_code == 404
        assert admin_client.put(target, {"first_name": "Changed"}).status_code == 404
        assert admin_client.delete(target).status_code == 404
        assert str(user.pk) not in {
            str(row["id"]) for row in admin_client.get(self.url).data["results"]
        }

    def test_delete_self_is_rejected(self, admin_client, superuser):
        response = admin_client.delete(f"{self.url}{superuser.pk}/")
        assert response.status_code == 400
        superuser.refresh_from_db()
        assert superuser.deleted_at is None
        assert superuser.is_active

    def test_delete_requires_admin(self, auth_client, user):
        other = UserFactory()
        assert auth_client.delete(f"{self.url}{other.pk}/").status_code == 403
        other.refresh_from_db()
        assert other.deleted_at is None

    def test_delete_requires_authentication(self, api_client, user):
        assert api_client.delete(f"{self.url}{user.pk}/").status_code == 401
        user.refresh_from_db()
        assert user.deleted_at is None

    def test_delete_missing_user(self, admin_client):
        from uuid import uuid4

        assert admin_client.delete(f"{self.url}{uuid4()}/").status_code == 404

    def test_deleted_user_cannot_authenticate(self, admin_client, user):
        from django.urls import reverse
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        assert admin_client.delete(f"{self.url}{user.pk}/").status_code == 204
        client = APIClient()
        response = client.get("/api/v1/users/me/", HTTP_AUTHORIZATION=f"Bearer {token}")
        assert response.status_code == 401
        response = client.post(
            reverse("auth:sign-in"),
            {
                "email": user.email,
                "password": "testpassword123!",
            },
        )
        assert response.status_code == 401
        response = client.post(reverse("auth:refresh"), {"refresh": str(refresh)})
        assert response.status_code == 401


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

    @pytest.mark.parametrize("is_superuser", [True, False])
    def test_cannot_suspend_own_account(self, api_client, is_superuser):
        admin = UserFactory(status="AC", is_superuser=is_superuser)
        admin.groups.add(Group.objects.get_or_create(name="admin")[0])
        api_client.force_authenticate(admin)

        response = api_client.put(f"/api/v1/users/{admin.pk}/modify_user_status/")

        assert response.status_code == 400
        assert response.data == {"error": "Cannot suspend your own account"}
        admin.refresh_from_db()
        assert admin.status == "AC"
        assert admin.is_active

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
            "/api/v1/users/me/", {"id": str(other.pk), "full_name": "Updated"}
        )
        assert response.status_code == 200
        user.refresh_from_db()
        other.refresh_from_db()
        assert user.first_name == "Updated"
        assert other.first_name == "Other"


@pytest.mark.django_db
class TestUserListFilters:
    url = "/api/v1/users/"

    @pytest.mark.parametrize(
        "value, stored_status",
        [("active", "AC"), ("pending", "PD"), ("suspended", "SA"), ("inactive", "NA")],
    )
    def test_status_filter(self, admin_client, value, stored_status):
        users = [UserFactory(status=s) for s in ["AC", "PD", "SA", "NA"]]
        response = admin_client.get(self.url, {"status": value})
        assert response.status_code == 200
        ids = {str(row["id"]) for row in response.data["results"]}
        for user in users:
            assert (str(user.pk) in ids) == (user.status == stored_status)

    @pytest.mark.parametrize("value", ["invalid", "AC", "ACTIVE", "suspend"])
    def test_invalid_status(self, admin_client, value):
        response = admin_client.get(self.url, {"status": value})
        assert response.status_code == 400
        assert "status" in response.data

    @pytest.mark.parametrize("field", ["email", "username", "first_name", "last_name"])
    def test_search(self, admin_client, field):
        value = "searchtarget@example.com" if field == "email" else "searchtarget"
        matching = UserFactory(**{field: value})
        UserFactory()
        response = admin_client.get(self.url, {"search": "SEARCHTARGET"})
        assert response.status_code == 200
        assert [str(row["id"]) for row in response.data["results"]] == [
            str(matching.pk)
        ]

    def test_combined_search_and_status(self, admin_client):
        matching = UserFactory(first_name="SearchTarget", status="SA")
        UserFactory(first_name="SearchTarget", status="AC")
        UserFactory(first_name="SomeoneElse", status="SA")
        response = admin_client.get(
            self.url, {"search": "SearchTarget", "status": "suspended"}
        )
        assert response.status_code == 200
        assert [str(row["id"]) for row in response.data["results"]] == [
            str(matching.pk)
        ]

    @pytest.mark.parametrize("field", ["created_at", "email", "username"])
    @pytest.mark.parametrize("descending", [False, True])
    def test_ordering(self, admin_client, field, descending):
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()
        older = UserFactory(
            first_name="OrderingTarget",
            email="a@example.com",
            username="aaa",
            created_at=now - timedelta(days=1),
        )
        newer = UserFactory(
            first_name="OrderingTarget",
            email="z@example.com",
            username="zzz",
            created_at=now,
        )
        ordering = f"-{field}" if descending else field
        response = admin_client.get(
            self.url, {"search": "OrderingTarget", "ordering": ordering}
        )
        assert response.status_code == 200
        expected = [newer, older] if descending else [older, newer]
        assert [str(row["id"]) for row in response.data["results"]] == [
            str(user.pk) for user in expected
        ]

    @pytest.mark.parametrize("ordering", [None, "password"])
    def test_default_ordering(self, admin_client, ordering):
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()
        newer = UserFactory(first_name="OrderingTarget", created_at=now)
        older = UserFactory(
            first_name="OrderingTarget", created_at=now - timedelta(days=1)
        )
        params = {"search": "OrderingTarget"}
        if ordering is not None:
            params["ordering"] = ordering
        response = admin_client.get(self.url, params)
        assert response.status_code == 200
        assert [str(row["id"]) for row in response.data["results"]] == [
            str(newer.pk),
            str(older.pk),
        ]

    @pytest.mark.parametrize("value", ["true", "false"])
    def test_unrelated_default_parameter_does_not_filter_status(
        self, admin_client, value
    ):
        user = UserFactory(status="AC")
        response = admin_client.get(self.url, {"default": value})
        assert response.status_code == 200
        assert str(user.pk) in {str(row["id"]) for row in response.data["results"]}
