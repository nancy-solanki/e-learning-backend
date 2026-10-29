import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import Group, Permission
from django.test import RequestFactory

from apps.localization.admin import LocalizationModelAdmin
from apps.localization.models import Localization
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.parametrize("role", ["instructor", "admin", "superuser"])
def test_admin_access_requires_admin(role):
    user = UserFactory(is_staff=True, is_superuser=role == "superuser")
    user.groups.add(Group.objects.get_or_create(name=role)[0])
    user.user_permissions.set(
        Permission.objects.filter(content_type__app_label="localization")
    )
    request = RequestFactory().get("/")
    request.user = user
    model_admin = LocalizationModelAdmin(Localization, AdminSite())
    for action in ["module", "view", "add", "change", "delete"]:
        assert getattr(model_admin, f"has_{action}_permission")(request) == (
            role in ("admin", "superuser")
        )
