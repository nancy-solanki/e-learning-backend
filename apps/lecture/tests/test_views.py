import pytest
from django.contrib.auth.models import Group

from apps.lecture.models import Lecture
from apps.lecture.tests.factories import LectureFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
PUBLIC = "/api/v1/lecture/"
MANAGE = PUBLIC + "instructor/all/"


def test_public_visibility_and_options(client, lecture):
    assert client.get(PUBLIC).data["count"] == 0
    lecture.status = "published"
    lecture.save()
    assert client.get(PUBLIC + f"{lecture.pk}/").status_code == 200
    assert client.options(PUBLIC).status_code == 200
    assert client.post(PUBLIC, {}).status_code == 405


def test_section_lookup(client, lecture):
    response = client.get(PUBLIC + f"section/{lecture.section.slug}/")
    assert response.status_code == 200
    assert response.data["results"][0]["id"] == str(lecture.pk)
    assert client.get(PUBLIC + "section/missing/").status_code == 404


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_management_requires_auth(client, lecture, method):
    target = MANAGE if method in ("get", "post") else MANAGE + f"{lecture.pk}/"
    assert getattr(client, method)(target).status_code == 401


def test_create_returns_saved_object_update_and_delete(client, lecture, instructor):
    client.force_authenticate(instructor)
    data = {
        "title": "New",
        "description": "Intro",
        "course": str(lecture.course_id),
        "section": str(lecture.section_id),
        "lecture_type": "document",
        "document_content": "Content",
        "duration": "10:00",
    }
    response = client.post(MANAGE, data, format="json")
    assert response.status_code == 201, response.data
    created = Lecture.objects.get(pk=response.data["id"])
    assert response.data["instructor"] == instructor.username
    assert created.instructor == instructor
    target = MANAGE + f"{created.pk}/"
    assert client.patch(target, {"title": "Updated"}, format="json").status_code == 200
    created.refresh_from_db()
    assert created.title == "Updated"
    assert client.delete(target).status_code == 200
    created.refresh_from_db()
    assert created.is_deleted


def test_foreign_hidden_and_student_denied(client, instructor):
    foreign = LectureFactory()
    client.force_authenticate(instructor)
    assert client.patch(MANAGE + f"{foreign.pk}/", {}).status_code == 404
    client.force_authenticate(UserFactory())
    assert client.get(MANAGE).status_code == 403


def test_admin_restore(client, lecture):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(user)
    lecture.soft_delete()
    assert client.delete(MANAGE + f"{lecture.pk}/").status_code == 200
    lecture.refresh_from_db()
    assert not lecture.is_deleted


@pytest.mark.parametrize("endpoint", [PUBLIC, MANAGE, "section"])
def test_combined_lecture_filters(client, instructor, endpoint):
    matching = LectureFactory(
        section__course__instructor=instructor,
        title="Python basics",
        status="published",
        is_preview=True,
    )
    LectureFactory(section=matching.section, status="published", title="Java basics")
    LectureFactory(status="published", title="Python basics", is_preview=True)
    if endpoint == MANAGE:
        client.force_authenticate(instructor)
    elif endpoint == "section":
        endpoint = PUBLIC + f"section/{matching.section.slug}/"
    response = client.get(
        endpoint,
        {
            "search": "pYtHoN",
            "course": str(matching.course_id),
            "course_slug": matching.course.slug.upper(),
            "section": str(matching.section_id),
            "section_slug": matching.section.slug.upper(),
            "instructor": str(instructor.pk),
            "status": "published",
            "lecture_type": "document",
            "is_preview": "true",
        },
    )
    assert response.status_code == 200, response.data
    assert [row["id"] for row in response.data["results"]] == [str(matching.pk)]


@pytest.mark.parametrize(
    "parameter",
    [
        "course",
        "course_slug",
        "section",
        "section_slug",
        "instructor",
        "status",
        "lecture_type",
        "is_preview",
    ],
)
def test_individual_lecture_filters(client, parameter):
    admin = UserFactory()
    admin.groups.add(Group.objects.get_or_create(name="admin")[0])
    client.force_authenticate(admin)
    matching = LectureFactory(status="published", is_preview=True)
    LectureFactory(status="draft", lecture_type="video", is_preview=False)
    values = {
        "course": str(matching.course_id),
        "course_slug": matching.course.slug.upper(),
        "section": str(matching.section_id),
        "section_slug": matching.section.slug.upper(),
        "instructor": str(matching.instructor_id),
        "status": "published",
        "lecture_type": "document",
        "is_preview": "true",
    }
    response = client.get(MANAGE, {parameter: values[parameter]})
    assert response.status_code == 200, response.data
    assert [row["id"] for row in response.data["results"]] == [str(matching.pk)]


@pytest.mark.parametrize("field", ["title", "description", "course", "section"])
def test_lecture_search_fields(client, field):
    lecture = LectureFactory(status="published")
    if field in ("course", "section"):
        related = getattr(lecture, field)
        related.title = "Unique search phrase"
        related.save()
    else:
        setattr(lecture, field, "Unique search phrase")
        lecture.save()
    LectureFactory(status="published")
    response = client.get(PUBLIC, {"search": "unique search"})
    assert [row["id"] for row in response.data["results"]] == [str(lecture.pk)]
    assert client.get(PUBLIC, {"search": "missing"}).data["count"] == 0


def test_lecture_filters_preserve_visibility_and_ownership(client, instructor):
    visible = LectureFactory(status="published", section__course__instructor=instructor)
    LectureFactory(status="draft", section=visible.section)
    deleted = LectureFactory(status="published", section=visible.section)
    deleted.soft_delete()
    inactive = LectureFactory(status="published")
    inactive.instructor.status = "IA"
    inactive.instructor.save()
    response = client.get(PUBLIC, {"search": "Introduction"})
    assert [row["id"] for row in response.data["results"]] == [str(visible.pk)]
    assert client.get(PUBLIC, {"status": "draft"}).data["count"] == 0
    client.force_authenticate(instructor)
    assert (
        client.get(MANAGE, {"instructor": str(inactive.instructor_id)}).data["count"]
        == 0
    )


def test_section_filters_cannot_expand_scope(client, lecture):
    foreign = LectureFactory()
    endpoint = PUBLIC + f"section/{lecture.section.slug}/"
    response = client.get(endpoint, {"section": str(foreign.section_id)})
    assert response.status_code == 200
    assert response.data["count"] == 0
    assert client.get(endpoint, {"search": "missing"}).data["count"] == 0


@pytest.mark.parametrize(
    "parameter", ["course", "section", "instructor", "status", "lecture_type"]
)
def test_invalid_lecture_filters(client, parameter):
    assert client.get(PUBLIC, {parameter: "invalid"}).status_code == 400


def test_lecture_ordering_and_false_preview_filter(client):
    later = LectureFactory(status="published", order=2, title="Alpha", is_preview=False)
    earlier = LectureFactory(status="published", order=1, title="Beta", is_preview=True)
    response = client.get(PUBLIC)
    assert [row["id"] for row in response.data["results"]] == [
        str(earlier.pk),
        str(later.pk),
    ]
    for ordering in ("-order", "title"):
        response = client.get(PUBLIC, {"ordering": ordering})
        assert [row["id"] for row in response.data["results"]] == [
            str(later.pk),
            str(earlier.pk),
        ]
    response = client.get(PUBLIC, {"is_preview": "false"})
    assert [row["id"] for row in response.data["results"]] == [str(later.pk)]
