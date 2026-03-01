from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):

    def create_user(self, email, username, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            username=username.lower(),
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("status", self.model.Status.ACTIVE)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            **extra_fields
        )
