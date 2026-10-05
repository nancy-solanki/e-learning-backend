import pytest

from apps.enroll.tests.factories import EnrollFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
BASE = "/api/v1/enroll/management/"


def test_auth_and_user_scoping(client, enroll):
    assert client.get(BASE).status_code == 401
    EnrollFactory()
    client.force_authenticate(enroll.user)
    response = client.get(BASE)
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == str(enroll.pk)
    assert client.get(BASE + f"{enroll.pk}/").status_code == 200
    client.force_authenticate(UserFactory())
    assert client.get(BASE + f"{enroll.pk}/").status_code == 404


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_read_only(client, enroll, method):
    client.force_authenticate(enroll.user)
    target = BASE if method == "post" else BASE + f"{enroll.pk}/"
    assert getattr(client, method)(target).status_code == 405


def test_instructor_and_search(client, enroll):
    enroll.course.instructor.become_instructor()
    client.force_authenticate(enroll.course.instructor)
    assert client.get(BASE, {"search": enroll.course.title}).data["count"] == 1
    assert client.get(BASE, {"search": "missing"}).data["count"] == 0


def test_course_lookup(client, enroll):
    client.force_authenticate(enroll.course.instructor)
    target = f"/api/v1/enroll/course/{enroll.course.slug}/"
    assert client.get(target).status_code == 404
    enroll.course.status = "published"
    enroll.course.save()
    response = client.get(target)
    assert response.status_code == 200
    assert response.data["results"][0]["id"] == str(enroll.pk)
    enroll.soft_delete()
    assert client.get(target).status_code == 404


@pytest.fixture(params=["management", "course"])
def filtered_enrollments(request, client, enroll):
    from datetime import datetime, timezone

    enroll.course.status = "published"
    enroll.course.save()
    enroll.course.instructor.become_instructor()
    enroll.user.first_name = "Alice"
    enroll.user.last_name = "Learner"
    enroll.user.username = "uniquelearner"
    enroll.user.email = "alice@example.com"
    enroll.user.save()
    enroll.created_at = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    enroll.save()
    other = EnrollFactory(course=enroll.course)
    other.created_at = datetime(2026, 1, 17, 12, tzinfo=timezone.utc)
    other.save()
    deleted = EnrollFactory(course=enroll.course, user=enroll.user)
    deleted.soft_delete()
    EnrollFactory(user=enroll.user)
    client.force_authenticate(enroll.course.instructor)
    url = (
        BASE
        if request.param == "management"
        else f"/api/v1/enroll/course/{enroll.course.slug}/"
    )
    return url, enroll, other


@pytest.mark.parametrize(
    "search", ["ALICE Learner", "uniquelearner", "alice@example.com"]
)
def test_search_fields_and_multiple_terms(client, filtered_enrollments, search):
    url, enroll, _ = filtered_enrollments
    response = client.get(url, {"search": search})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(enroll.pk)]


def test_combined_filters(client, filtered_enrollments):
    url, enroll, _ = filtered_enrollments
    query = {
        "course": str(enroll.course_id),
        "course_slug": enroll.course.slug.upper(),
        "user": str(enroll.user_id),
        "created_at_after": "2026-01-15",
        "created_at_before": "2026-01-15",
        "search": "Alice Learner",
    }
    response = client.get(url, query)
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(enroll.pk)]


@pytest.mark.parametrize(
    "field", ["course", "user", "created_at_after", "created_at_before"]
)
def test_invalid_filters(client, filtered_enrollments, field):
    url, _, _ = filtered_enrollments
    assert client.get(url, {field: "invalid"}).status_code == 400


@pytest.mark.parametrize("field", ["course", "user", "course_slug"])
def test_filters_no_match(client, filtered_enrollments, field):
    url, _, _ = filtered_enrollments
    foreign = EnrollFactory()
    value = {
        "course": str(foreign.course_id),
        "user": str(foreign.user_id),
        "course_slug": foreign.course.slug,
    }[field]
    response = client.get(url, {field: value})
    assert response.status_code == 200
    assert response.data["count"] == 0


@pytest.mark.parametrize(
    "query,which",
    [
        ({"created_at_after": "2026-01-16"}, "other"),
        ({"created_at_before": "2026-01-16"}, "enroll"),
    ],
)
def test_date_boundaries(client, filtered_enrollments, query, which):
    url, enroll, other = filtered_enrollments
    expected = enroll if which == "enroll" else other
    response = client.get(url, query)
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(expected.pk)]


@pytest.mark.parametrize("ordering", ["created_at", "-created_at"])
def test_ordering(client, filtered_enrollments, ordering):
    url, enroll, other = filtered_enrollments
    expected = [enroll, other] if ordering == "created_at" else [other, enroll]
    response = client.get(url, {"ordering": ordering})
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [
        str(row.pk) for row in expected
    ]


def test_user_filter_preserves_student_scope(client, enroll):
    foreign = EnrollFactory(course=enroll.course)
    client.force_authenticate(enroll.user)
    response = client.get(BASE, {"user": str(foreign.user_id)})
    assert response.status_code == 200
    assert response.data["count"] == 0
