"""Contract checks: generation must not read records or silently omit payloads."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema
from rest_framework.test import APIClient


@pytest.fixture(scope="module")
def schema():
    # No django_db marker: any accidental database access fails this fixture.
    result = SchemaGenerator().get_schema(request=None, public=True)
    validate_schema(result)
    return result


def test_schema_generation_has_no_warnings():
    output = StringIO()
    errors = StringIO()
    call_command(
        "spectacular", validate=True, fail_on_warn=True, stdout=output, stderr=errors
    )
    assert not errors.getvalue()


def test_every_operation_has_metadata_and_success_contract(schema):
    ids = []
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            assert operation["summary"], (path, method)
            assert operation["description"], (path, method)
            assert operation["tags"], (path, method)
            ids.append(operation["operationId"])
            successful = {
                code: value
                for code, value in operation["responses"].items()
                if code.startswith("2")
            }
            assert successful, (path, method)
            for code, response in successful.items():
                if code == "204":
                    assert "content" not in response
                else:
                    assert response["content"]["application/json"]["schema"], (
                        path,
                        method,
                    )
    assert len(ids) == len(set(ids))


def test_component_references_resolve(schema):
    def walk(value):
        if isinstance(value, dict):
            if "$ref" in value:
                target = schema
                for part in value["$ref"].removeprefix("#/").split("/"):
                    target = target[part]
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(schema)


def test_custom_contracts(schema):
    paths = schema["paths"]
    wallet = paths["/api/v1/wallet/"]["get"]
    assert wallet["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/WalletResponse"
    }
    assert "page" not in {p["name"] for p in wallet.get("parameters", [])}
    assert (
        "requestBody" not in paths["/api/v1/users/{id}/modify_admin_privileges/"]["put"]
    )
    assert "204" in paths["/api/v1/auth/sign-out/"]["post"]["responses"]
    for endpoint in (
        "sign-up",
        "sign-in",
        "staff/sign-in",
        "change-password",
        "google",
        "apple",
    ):
        operation = paths[f"/api/v1/auth/{endpoint}/"]["post"]
        assert operation["requestBody"]["content"]["application/json"]["schema"]
    assert (
        "multipart/form-data"
        in paths["/api/v1/category/"]["post"]["requestBody"]["content"]
    )
    components = schema["components"]["schemas"]
    assert (
        components["CategoryUploadRequest"]["properties"]["thumbnail"]["format"]
        == "binary"
    )
    assert components["UserProfileResponse"]["properties"]["avatar"]["format"] == "uri"
    assert (
        components["PatchedUserProfileRequest"]["properties"]["avatar"]["format"]
        == "binary"
    )
    assert (
        components["FilteredCourse"]["properties"]["student_count"]["type"] == "integer"
    )
    assert components["Enroll"]["properties"]["progress"]["type"] == "integer"
    verification = components["SuccessPaymentRequest"]["properties"]["response"][
        "oneOf"
    ]
    assert {variant["type"] for variant in verification} == {"object", "string"}
    assert "password" not in components["PublicUser"]["properties"]
    assert "email" not in components["PublicUser"]["properties"]


@pytest.mark.parametrize("name", ["schema", "swagger-ui", "redoc"])
@pytest.mark.django_db
def test_documentation_requires_admin(name):
    from apps.users.tests.factories import SuperuserFactory, UserFactory

    client = APIClient()
    assert client.get(reverse(name)).status_code == 401
    client.force_authenticate(UserFactory())
    assert client.get(reverse(name)).status_code == 403
    client.force_authenticate(SuperuserFactory())
    response = client.get(reverse(name))
    assert response.status_code == 200


@pytest.mark.parametrize("resource", ["rating", "enroll", "order"])
@pytest.mark.django_db
def test_nested_identity_does_not_expose_account_details(resource):
    from apps.enroll.serializers import EnrollSerializer
    from apps.enroll.tests.factories import EnrollFactory
    from apps.order.serializers import OrderSerializer
    from apps.order.tests.factories import OrderFactory
    from apps.rating.serializers import RatingSerializer
    from apps.rating.tests.factories import RatingFactory

    factory, serializer = {
        "rating": (RatingFactory, RatingSerializer),
        "enroll": (EnrollFactory, EnrollSerializer),
        "order": (OrderFactory, OrderSerializer),
    }[resource]
    data = serializer(factory()).data
    for key in ("user", "instructor"):
        if key in data:
            assert set(data[key]) == {
                "id",
                "username",
                "first_name",
                "last_name",
                "full_name",
                "avatar",
            }


@pytest.mark.django_db
def test_course_roster_isolation():
    from apps.enroll.tests.factories import EnrollFactory
    from apps.users.tests.factories import UserFactory

    enrollment = EnrollFactory(course__status="published")
    other = EnrollFactory(course=enrollment.course)
    client = APIClient()
    url = f"/api/v1/enroll/course/{enrollment.course.slug}/"
    client.force_authenticate(UserFactory())
    assert client.get(url).status_code == 404
    client.force_authenticate(enrollment.user)
    assert [row["id"] for row in client.get(url).data["results"]] == [
        str(enrollment.pk)
    ]
    client.force_authenticate(enrollment.course.instructor)
    assert {row["id"] for row in client.get(url).data["results"]} == {
        str(enrollment.pk),
        str(other.pk),
    }
