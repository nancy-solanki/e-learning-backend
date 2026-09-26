from uuid import uuid4

import pytest
from django.urls import reverse

from apps.coupon.models import Coupon
from apps.coupon.tests.factories import CouponFactory
from apps.users.tests.factories import SuperuserFactory, UserFactory

pytestmark = pytest.mark.django_db


def url(coupon=None):
    if coupon:
        return reverse("coupon:coupon-management-detail", kwargs={"pk": coupon.pk})
    return reverse("coupon:coupon-management-list")


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
def test_anonymous_denied(client, coupon, method):
    target = url() if method in ("get", "post") else url(coupon)
    assert getattr(client, method)(target).status_code == 401


def test_student_cannot_manage(client):
    client.force_authenticate(UserFactory())
    assert client.get(url()).status_code == 403


def test_instructor_create_and_list(client, instructor, course):
    client.force_authenticate(instructor)
    response = client.post(
        url(), {"code": "SAVE", "course": str(course.pk)}, format="json"
    )
    assert response.status_code == 201, response.data
    assert Coupon.objects.get(code="SAVE").course == course
    CouponFactory()
    response = client.get(url())
    assert response.data["count"] == 1
    assert response.data["results"][0]["code"] == "SAVE"


@pytest.mark.parametrize("course_id", [None, "invalid", str(uuid4())])
def test_invalid_course_denied(client, instructor, course_id):
    client.force_authenticate(instructor)
    response = client.post(url(), {"code": "SAVE", "course": course_id}, format="json")
    assert response.status_code == 403
    assert not Coupon.objects.exists()


def test_foreign_course_create_denied(client, course):
    client.force_authenticate(UserFactory())
    assert (
        client.post(url(), {"code": "SAVE", "course": str(course.pk)}).status_code
        == 403
    )


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_foreign_coupon_hidden(client, instructor, method):
    coupon = CouponFactory()
    client.force_authenticate(instructor)
    assert getattr(client, method)(url(coupon)).status_code == 404


def test_admin_updates_deletes_and_restores(client, coupon):
    client.force_authenticate(SuperuserFactory())
    response = client.patch(url(coupon), {"value": 25}, format="json")
    assert response.status_code == 200
    coupon.refresh_from_db()
    assert coupon.value == 25
    assert client.delete(url(coupon)).status_code == 200
    coupon.refresh_from_db()
    assert coupon.is_deleted
    assert client.delete(url(coupon)).status_code == 200
    coupon.refresh_from_db()
    assert not coupon.is_deleted


def test_validate_coupon_endpoint(client, coupon):
    target = reverse("coupon:get-coupon", kwargs={"code": coupon.code})
    assert client.get(target).status_code == 401
    client.force_authenticate(UserFactory())
    response = client.get(target)
    assert response.status_code == 200
    assert response.data["id"] == str(coupon.pk)
    coupon.soft_delete()
    response = client.get(target)
    assert response.status_code == 404
    assert response.data["errors"] == ["Coupon not found!"]


@pytest.mark.parametrize(
    "query",
    [
        {"search": "MATCH"},
        {"is_global": "true"},
        {"coupon_type": "FIXED"},
        {"is_unlimited": "true"},
    ],
)
def test_filters(client, query):
    client.force_authenticate(SuperuserFactory())
    matching = CouponFactory(
        code="MATCH", is_global=True, coupon_type="fixed", is_unlimited=True
    )
    CouponFactory()
    response = client.get(url(), query)
    assert [row["id"] for row in response.data["results"]] == [str(matching.pk)]
