import uuid

import pytest

from apps.localization.tests.factories import LocalizationFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
MANAGE = "/api/v1/course/instructor/all/"
LOOKUP = "/api/v1/course/localizations/"


@pytest.mark.parametrize("format", ["json", "multipart"])
def test_set_preserve_and_clear_localization(client, course, format):
    client.force_authenticate(course.instructor)
    localization = LocalizationFactory()
    target = MANAGE + f"{course.pk}/"
    response = client.patch(
        target, {"localization": str(localization.pk)}, format=format
    )
    assert response.status_code == 200, response.data
    assert str(response.data["localization"]) == str(localization.pk)
    course.refresh_from_db()
    assert course.localization == localization
    response = client.patch(target, {"title": "Updated"}, format=format)
    assert response.status_code == 200
    course.refresh_from_db()
    assert course.localization == localization
    response = client.patch(
        target, {"localization": None if format == "json" else ""}, format=format
    )
    assert response.status_code == 200, response.data
    assert response.data["localization"] is None
    course.refresh_from_db()
    assert course.localization is None


@pytest.mark.parametrize("kind", ["missing", "deleted", "invalid"])
def test_invalid_localization_does_not_modify_course(client, course, kind):
    client.force_authenticate(course.instructor)
    if kind == "deleted":
        localization = LocalizationFactory()
        localization.soft_delete()
        value = str(localization.pk)
    else:
        value = str(uuid.uuid4()) if kind == "missing" else "invalid"
    response = client.patch(
        MANAGE + f"{course.pk}/", {"localization": value}, format="json"
    )
    assert response.status_code == 400
    assert "localization" in response.data
    course.refresh_from_db()
    assert course.localization is None


def test_lookup_only_exposes_active_localizations(client, instructor):
    active = LocalizationFactory(language_name="English")
    deleted = LocalizationFactory()
    deleted.soft_delete()
    assert client.get(LOOKUP).status_code == 401
    client.force_authenticate(UserFactory())
    assert client.get(LOOKUP).status_code == 403
    client.force_authenticate(instructor)
    response = client.get(LOOKUP)
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(active.pk)
    assert response.data["results"][0]["language_name"] == "English"


def test_public_course_localization_and_hard_delete(client, course):
    localization = LocalizationFactory()
    course.localization = localization
    course.status = "published"
    course.save()
    response = client.get(f"/api/v1/course/{course.slug}/")
    assert response.status_code == 200
    assert str(response.data["localization"]) == str(localization.pk)
    localization.delete()
    course.refresh_from_db()
    assert course.localization is None
