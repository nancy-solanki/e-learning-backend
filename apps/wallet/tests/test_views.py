from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser, Group

from apps.users.tests.factories import UserFactory
from apps.wallet.tests.factories import WalletFactory
from apps.wallet.views import IsInstructorOrAdmin

pytestmark = pytest.mark.django_db
BASE = "/api/v1/wallet/"


def test_anonymous_and_student_denied(client):
    assert client.get(BASE).status_code == 401
    client.force_authenticate(UserFactory())
    assert client.get(BASE).status_code == 403
    assert not IsInstructorOrAdmin().has_permission(
        SimpleNamespace(user=AnonymousUser()), None
    )


@pytest.mark.parametrize("role", ["instructor", "admin"])
def test_owner_can_read_wallet(client, wallet, role):
    wallet.user.groups.add(Group.objects.get_or_create(name=role)[0])
    client.force_authenticate(wallet.user)
    assert client.get(BASE).data["id"] == str(wallet.pk)
    assert client.get(BASE + f"{wallet.pk}/").status_code == 200
    foreign = WalletFactory()
    assert client.get(BASE + f"{foreign.pk}/").status_code == 404


def test_missing_and_deleted_wallet(client, wallet):
    wallet.user.become_instructor()
    client.force_authenticate(wallet.user)
    wallet.soft_delete()
    response = client.get(BASE)
    assert response.status_code == 404
    assert response.data == {"detail": "Wallet not found."}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_readonly(client, wallet, method):
    wallet.user.become_instructor()
    client.force_authenticate(wallet.user)
    target = BASE if method == "post" else BASE + f"{wallet.pk}/"
    assert getattr(client, method)(target).status_code == 405
