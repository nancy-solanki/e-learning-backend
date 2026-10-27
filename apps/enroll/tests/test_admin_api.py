import csv
from io import StringIO

import pytest
from django.contrib.auth.models import Group

from apps.enroll.tests.factories import EnrollFactory
from apps.lecture.tests.factories import LectureFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/enroll/management/"


@pytest.fixture
def admin_client(client):
    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(admin)
    return client


@pytest.mark.parametrize("role", [None, "student", "instructor"])
def test_admin_endpoints_deny_non_admins(client, enroll, role):
    if role:
        user = UserFactory()
        user.groups.add(Group.objects.get_or_create(name=role)[0])
        client.force_authenticate(user)
    for suffix in ("summary/", "courses/", "export/"):
        assert client.get(BASE + suffix).status_code == (403 if role else 401)


def test_superuser_can_read_all_enrollments(client, enroll):
    client.force_authenticate(UserFactory(is_superuser=True))
    assert client.get(BASE).data["count"] == 1


def test_admin_role_takes_precedence_over_instructor(client, enroll):
    user = UserFactory()
    user.become_instructor()
    user.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(user)
    assert client.get(BASE).data["count"] == 1
    assert client.get(f"{BASE}{enroll.pk}/").status_code == 200


def test_shared_endpoint_preserves_non_admin_scope_and_privacy(client, enroll):
    foreign = EnrollFactory()
    enroll.course.instructor.become_instructor()
    for user in (enroll.user, enroll.course.instructor):
        client.force_authenticate(user)
        response = client.get(BASE)
        assert response.data["count"] == 1
        row = response.data["results"][0]
        assert row["id"] == str(enroll.pk)
        assert "email" not in row["user"]
        assert row["progress"] == 0
        assert client.get(f"{BASE}{foreign.pk}/").status_code == 404


def test_admin_can_read_published_course_roster(admin_client, enroll):
    enroll.course.status = "published"
    enroll.course.save()
    response = admin_client.get(f"/api/v1/enroll/course/{enroll.course.slug}/")
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_list_detail_and_lesson_counts(admin_client, enroll):
    other = EnrollFactory()
    deleted = EnrollFactory()
    deleted.soft_delete()
    published = LectureFactory(
        course=enroll.course, status="published", section__status="published"
    )
    LectureFactory(course=enroll.course, status="draft", section=published.section)
    removed = LectureFactory(
        course=enroll.course, status="published", section=published.section
    )
    removed.soft_delete()
    LectureFactory(course=enroll.course, status="published", section__status="draft")
    response = admin_client.get(BASE)
    assert response.status_code == 200
    assert response.data["count"] == 2
    assert {row["id"] for row in response.data["results"]} == {
        str(enroll.pk),
        str(other.pk),
    }
    detail = admin_client.get(f"{BASE}{enroll.pk}/").data
    assert detail["user"]["email"] == enroll.user.email
    assert detail["course"]["id"] == str(enroll.course_id)
    assert detail["total_lessons"] == 1
    assert detail["progress"] is None
    assert detail["completed_lessons"] is None
    assert detail["status"] == "unknown"
    assert detail["access"] is None
    assert detail["progress_tracking_available"] is False
    assert admin_client.get(f"{BASE}{deleted.pk}/").status_code == 404


def test_filters_summary_and_export_agree(admin_client, enroll):
    EnrollFactory()
    query = {"course": str(enroll.course_id), "search": str(enroll.pk)}
    assert admin_client.get(BASE, query).data["count"] == 1
    summary = admin_client.get(BASE + "summary/", query).data
    assert summary == {
        "total_enrollments": 1,
        "unknown": 1,
        "in_progress": None,
        "completed": None,
        "not_started": None,
        "progress_tracking_available": False,
    }
    response = admin_client.get(BASE + "export/", query)
    assert response["Content-Type"].startswith("text/csv")
    rows = list(csv.reader(StringIO(response.content.decode())))
    assert len(rows) == 2
    assert rows[1][0] == str(enroll.pk)
    assert rows[1][2] == enroll.user.email
    assert rows[1][6:9] == ["", "", "unknown"]


def test_course_options_are_unique_and_exclude_deleted_enrollments(
    admin_client, enroll
):
    EnrollFactory(course=enroll.course)
    deleted = EnrollFactory()
    deleted.soft_delete()
    response = admin_client.get(BASE + "courses/")
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(enroll.course_id)


def test_export_is_not_paginated_and_escapes_formulas(admin_client, enroll):
    enroll.user.first_name = "=HYPERLINK(1)"
    enroll.user.save()
    EnrollFactory.create_batch(21, course=enroll.course, user=enroll.user)
    assert len(admin_client.get(BASE).data["results"]) == 20
    assert admin_client.get(BASE + "summary/").data["total_enrollments"] == 22
    response = admin_client.get(BASE + "export/", {"page": 2})
    rows = list(csv.reader(StringIO(response.content.decode())))
    assert len(rows) == 23
    assert all(row[1].startswith("'=HYPERLINK") for row in rows[1:])


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_admin_api_is_read_only(admin_client, enroll, method):
    target = BASE if method == "post" else f"{BASE}{enroll.pk}/"
    assert getattr(admin_client, method)(target).status_code == 405


def test_invalid_course_filter_returns_400(admin_client):
    for suffix in ("", "summary/", "export/"):
        assert admin_client.get(BASE + suffix, {"course": "invalid"}).status_code == 400
