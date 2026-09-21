import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating User instances in tests."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpassword123!")
    status = User.Status.ACTIVE
    gender = User.Gender.MALE


class SuperuserFactory(UserFactory):
    """Factory for creating superuser instances in tests."""

    is_superuser = True
    is_staff = True
    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    username = factory.Sequence(lambda n: f"admin{n}")
