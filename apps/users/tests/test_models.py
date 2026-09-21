import pytest
from django.contrib.auth import get_user_model

from apps.users.tests.factories import UserFactory

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Tests for the User model fields, defaults and save behaviour."""

    def test_create_user_with_factory(self):
        user = UserFactory()
        assert user.pk is not None
        assert user.email is not None

    def test_email_is_lowercased_on_save(self):
        user = UserFactory(email="Test@Example.COM")
        assert user.email == "test@example.com"

    def test_username_is_lowercased_on_save(self):
        user = UserFactory(username="TestUser")
        assert user.username == "testuser"

    def test_default_status_is_active_via_factory(self):
        user = UserFactory()
        assert user.status == User.Status.ACTIVE

    def test_default_gender_is_male(self):
        user = UserFactory()
        assert user.gender == User.Gender.MALE

    def test_str_returns_email(self):
        user = UserFactory(email="hello@example.com")
        assert str(user) == "hello@example.com"

    def test_account_activity_default_true(self):
        user = UserFactory()
        assert user.account_activity is True

    def test_email_notifications_default_true(self):
        user = UserFactory()
        assert user.email_notifications is True

    def test_message_notifications_default_true(self):
        user = UserFactory()
        assert user.message_notifications is True

    def test_uuid_primary_key(self):
        user = UserFactory()
        import uuid

        assert isinstance(user.pk, uuid.UUID)

    def test_created_at_is_set(self):
        user = UserFactory()
        assert user.created_at is not None

    def test_email_uniqueness(self):
        from django.db import IntegrityError

        UserFactory(email="unique@example.com")
        with pytest.raises(IntegrityError):
            UserFactory(email="unique@example.com")

    def test_username_uniqueness(self):
        from django.db import IntegrityError

        UserFactory(username="uniqueuser")
        with pytest.raises(IntegrityError):
            UserFactory(username="uniqueuser")

    def test_pending_status(self):
        user = UserFactory(status=User.Status.PENDING)
        assert user.status == User.Status.PENDING

    def test_inactive_status(self):
        user = UserFactory(status=User.Status.INACTIVE)
        assert user.status == User.Status.INACTIVE

    def test_female_gender(self):
        user = UserFactory(gender=User.Gender.FEMALE)
        assert user.gender == User.Gender.FEMALE
