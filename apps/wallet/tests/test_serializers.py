import pytest

from apps.wallet.serializers import WalletSerializer

pytestmark = pytest.mark.django_db


def test_representation(wallet):
    data = WalletSerializer(wallet).data
    assert data["id"] == str(wallet.pk)
    assert data["user"] == wallet.user_id
    assert data["current_earnings"] == 0
    assert data["total_earnings"] == 0
    assert data["total_withdraws"] == 0


@pytest.mark.parametrize(
    "field", ["current_earnings", "total_earnings", "total_withdraws"]
)
def test_invalid_integer(wallet, field):
    serializer = WalletSerializer(wallet, data={field: "invalid"}, partial=True)
    assert not serializer.is_valid()
    assert field in serializer.errors
