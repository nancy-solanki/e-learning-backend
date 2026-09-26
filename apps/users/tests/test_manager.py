import pytest

from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_create_user_hashes_password_and_normalizes():
    user = User.objects.create_user(
        "NEWUSER", "New@Example.COM", "New", "User", "Secret123!"
    )
    user.refresh_from_db()
    assert user.email == "new@example.com"
    assert user.username == "newuser"
    assert user.check_password("Secret123!")
    assert user.password != "Secret123!"
    assert not user.is_staff
    assert not user.is_superuser
    assert user.status == User.Status.PENDING


@pytest.mark.parametrize("email", [None, ""])
def test_missing_email_rejected(email):
    with pytest.raises(ValueError, match="email address"):
        User.objects.create_user("new", email, "New", "User", "Secret123!")
    assert not User.objects.exists()


def test_create_superuser_persists_admin_role():
    user = User.objects.create_superuser(
        "ADMIN", "Admin@Example.COM", "Admin", "User", "Secret123!"
    )
    user.refresh_from_db()
    assert user.is_superuser and user.is_staff and user.is_admin
    assert user.groups.filter(name="admin").exists()
    assert user.status == User.Status.ACTIVE
    assert user.check_password("Secret123!")
