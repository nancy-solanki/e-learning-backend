import pytest
from django.contrib.auth.models import Group

from apps.localization.service import LocalizationService
from apps.users.tests.factories import SuperuserFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", ["student", "admin", "superuser"])
def test_visibility_and_toggle(localization, role):
    user = SuperuserFactory() if role == "superuser" else UserFactory()
    if role == "admin":
        user.groups.add(Group.objects.get_or_create(name="admin")[0])
    assert list(LocalizationService.get_queryset_for_user(user)) == [localization]
    LocalizationService.toggle_localization_status(localization)
    assert list(LocalizationService.get_queryset_for_user(user)) == (
        [] if role == "student" else [localization]
    )
    LocalizationService.toggle_localization_status(localization)
    localization.refresh_from_db()
    assert not localization.is_deleted
