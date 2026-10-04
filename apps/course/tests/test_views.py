import pytest
from django.contrib.auth.models import Group

from apps.category.tests.factories import CategoryFactory
from apps.common.tests.factories import FileFactory
from apps.course.models import Course
from apps.course.tests.factories import CourseFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db
PUBLIC = "/api/v1/course/"
MANAGE = PUBLIC + "instructor/all/"


def test_public_list_detail_search(client, course):
    assert client.get(PUBLIC).data["count"] == 0
    course.status = "published"
    course.save()
    assert client.get(PUBLIC + course.slug + "/").status_code == 200
    assert client.get(PUBLIC, {"search": course.title}).data["count"] == 1
    assert client.get(PUBLIC, {"search": "no match"}).data["count"] == 0


def test_category_lookup(client, course):
    category = CategoryFactory()
    course.categories.add(category)
    course.status = "published"
    course.save()
    response = client.get(PUBLIC + f"category/{category.slug}/")
    assert response.status_code == 200
    assert [row["id"] for row in response.data["results"]] == [str(course.pk)]
    assert client.get(PUBLIC + "category/missing/").status_code == 404


@pytest.mark.parametrize("method", ["get", "post", "patch", "delete"])
def test_management_requires_auth(client, course, method):
    target = MANAGE if method in ("get", "post") else MANAGE + f"{course.pk}/"
    assert getattr(client, method)(target).status_code == 401


def test_instructor_create_update_and_delete(client, instructor):
    client.force_authenticate(instructor)
    category = CategoryFactory()
    payload = {
        "title": "New",
        "short_description": "Short",
        "long_description": "Long",
        "learn_description_points": "Basics",
        "requirements": "None",
        "thumbnail": str(FileFactory().pk),
        "categories": [str(category.pk)],
    }
    response = client.post(MANAGE, payload, format="json")
    assert response.status_code == 201, response.data
    course = Course.objects.get(pk=response.data["id"])
    assert course.instructor == instructor
    target = MANAGE + f"{course.pk}/"
    assert client.patch(target, {"title": "Updated"}, format="json").status_code == 200
    course.refresh_from_db()
    assert course.title == "Updated"
    assert client.delete(target).status_code == 204
    course.refresh_from_db()
    assert course.is_deleted


def test_foreign_course_hidden_and_student_denied(client, instructor):
    foreign = CourseFactory()
    client.force_authenticate(instructor)
    assert client.patch(MANAGE + f"{foreign.pk}/", {}).status_code == 404
    client.force_authenticate(UserFactory())
    assert client.get(MANAGE).status_code == 403


def test_admin_can_restore(client, course):
    user = UserFactory()
    user.groups.add(Group.objects.get_or_create(name="admin")[0])
    course.soft_delete()
    client.force_authenticate(user)
    assert client.delete(MANAGE + f"{course.pk}/").status_code == 200
    course.refresh_from_db()
    assert not course.is_deleted


@pytest.mark.parametrize("endpoint", [PUBLIC, "category", MANAGE])
def test_combined_course_filters(client, instructor, endpoint):
    from apps.course.models import Tag

    category = CategoryFactory()
    tag = Tag.objects.create(name="Web development")
    matching = CourseFactory(
        instructor=instructor,
        title="Django basics",
        status="published",
        price=100,
        is_best_seller=True,
    )
    matching.categories.add(category)
    matching.tags.add(tag)
    other = CourseFactory(instructor=instructor, status="published", price=200)
    other.categories.add(category)
    if endpoint == MANAGE:
        client.force_authenticate(instructor)
    elif endpoint == "category":
        endpoint = PUBLIC + f"category/{category.slug}/"
    response = client.get(
        endpoint,
        {
            "search": "django",
            "category": str(category.pk),
            "category_slug": category.slug,
            "tag": str(tag.pk),
            "tag_slug": tag.slug,
            "instructor": str(instructor.pk),
            "price_min": 100,
            "price_max": 100,
            "is_free": "false",
            "is_best_seller": "true",
        },
    )
    assert response.status_code == 200, response.data
    assert [row["id"] for row in response.data["results"]] == [str(matching.pk)]


def test_filters_preserve_public_visibility(client):
    published = CourseFactory(status="published", is_free=True)
    CourseFactory(status="draft", is_free=True)
    deleted = CourseFactory(status="published", is_free=True)
    deleted.soft_delete()
    inactive = CourseFactory(status="published", is_free=True)
    inactive.instructor.status = "IA"
    inactive.instructor.save()
    response = client.get(PUBLIC, {"is_free": "true"})
    assert [row["id"] for row in response.data["results"]] == [str(published.pk)]


def test_management_status_search_preserves_ownership(client, instructor):
    own = CourseFactory(instructor=instructor, status="draft", title="Django")
    CourseFactory(status="draft", title="Django")
    CourseFactory(instructor=instructor, status="published", title="Django")
    client.force_authenticate(instructor)
    response = client.get(MANAGE, {"status": "draft", "search": "Django"})
    assert [row["id"] for row in response.data["results"]] == [str(own.pk)]


@pytest.mark.parametrize(
    "params",
    [
        {"category": "invalid"},
        {"tag": "invalid"},
        {"instructor": "invalid"},
        {"price_min": "invalid"},
    ],
)
def test_invalid_course_filters(client, params):
    assert client.get(PUBLIC, params).status_code == 400


def test_related_search_has_no_duplicates_and_supports_ordering(client):
    first = CourseFactory(status="published", price=10)
    second = CourseFactory(status="published", price=20)
    categories = [
        CategoryFactory(title="Web design"),
        CategoryFactory(title="Web apps"),
    ]
    first.categories.add(*categories)
    second.categories.add(*categories)
    response = client.get(PUBLIC, {"search": "web", "ordering": "-price"})
    assert response.data["count"] == 2
    assert [row["id"] for row in response.data["results"]] == [
        str(second.pk),
        str(first.pk),
    ]
