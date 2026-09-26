import pytest

from apps.localization.serializers import LocalizationSerializer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("field", ["language_name", "country"])
@pytest.mark.parametrize("value", ["", "   ", "x" * 101, None])
def test_invalid_fields(field, value):
    data = {"language_name": "English", "country": "India", field: value}
    serializer = LocalizationSerializer(data=data)
    assert not serializer.is_valid()
    assert field in serializer.errors


def test_partial_update(localization):
    serializer = LocalizationSerializer(
        localization, data={"country": "UK"}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    localization.refresh_from_db()
    assert localization.country == "UK"
