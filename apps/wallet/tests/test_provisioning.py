import pytest
from django.contrib.auth.models import Group

from apps.users.models import User
from apps.users.tests.factories import UserFactory
from apps.wallet.models import Wallet

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("role", ["admin", "instructor", "student"])
@pytest.mark.parametrize("reverse", [False, True])
def test_role_assignment_provisions_only_earning_roles(role, reverse):
    user = UserFactory()
    group = Group.objects.get_or_create(name=role)[0]
    if reverse:
        group.user_set.add(user)
    else:
        user.groups.add(group)
    assert Wallet.objects.filter(user=user).count() == (role != "student")


def test_superuser_creation_creates_one_empty_wallet():
    user = User.objects.create_superuser(
        "admin", "admin@example.com", "Admin", "User", "Secret123!"
    )
    user.save()
    wallet = Wallet.objects.get(user=user)
    assert not wallet.is_site_wallet
    assert (
        wallet.current_earnings == wallet.total_earnings == wallet.total_withdraws == 0
    )


def test_multiple_roles_preserve_existing_disabled_wallet():
    user = UserFactory()
    user.become_instructor()
    wallet = Wallet.objects.get(user=user)
    wallet.current_earnings = 100
    wallet.save()
    wallet.soft_delete()
    user.toggle_admin_privileges()
    user.save()
    wallet.refresh_from_db()
    assert Wallet.objects.filter(user=user).count() == 1
    assert wallet.current_earnings == 100
    assert wallet.deleted_at is not None


def test_plain_user_has_no_wallet():
    user = UserFactory(is_staff=True)
    assert not Wallet.objects.filter(user=user).exists()
