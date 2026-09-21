from django.contrib.auth.models import BaseUserManager, Group


class UserManager(BaseUserManager):
    def create_user(self, username, email, first_name, last_name, password):
        """
        Creates and saves a regular user with the given email, first name, last name,
        and password. This user will only be assigned to the 'student' group.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            username=username,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, first_name, last_name, password):
        """
        Creates and saves a superuser with the given email, first name, last name,
        and password. This user will only be assigned to the 'admin' group.
        """
        user = self.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )

        group, _ = Group.objects.get_or_create(name="admin")
        user.groups.add(group)

        user.status = "AC"
        user.is_superuser = True
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)

        return user
