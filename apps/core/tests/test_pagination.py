import pytest
from rest_framework.test import APIClient

from apps.category.tests.factories import CategoryFactory
from apps.course.tests.factories import CourseFactory
from apps.enroll.tests.factories import EnrollFactory
from apps.lecture.tests.factories import LectureFactory
from apps.rating.tests.factories import RatingFactory
from apps.section.tests.factories import SectionFactory
from apps.users.tests.factories import SuperuserFactory, UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "collection", ["course", "section", "lecture", "enroll", "rating", "users"]
)
def test_default_pagination_across_collection_endpoints(collection):
    client = APIClient()
    if collection == "users":
        admin = SuperuserFactory()
        client.force_authenticate(admin)
        records = [admin, *UserFactory.create_batch(20)]
        url = "/api/v1/users/"
    else:
        course = CourseFactory(status="published")
        client.force_authenticate(course.instructor)
        if collection == "course":
            category = CategoryFactory()
            records = [
                course,
                *CourseFactory.create_batch(
                    20, status="published", instructor=course.instructor
                ),
            ]
            for record in records:
                record.categories.add(category)
            url = f"/api/v1/course/category/{category.slug}/"
        elif collection == "section":
            records = [SectionFactory(course=course, order=i) for i in range(21)]
            url = f"/api/v1/section/course/{course.slug}/"
        elif collection == "lecture":
            section = SectionFactory(course=course)
            records = [LectureFactory(section=section, order=i) for i in range(21)]
            url = f"/api/v1/lecture/section/{section.slug}/"
        elif collection == "enroll":
            records = EnrollFactory.create_batch(21, course=course)
            url = f"/api/v1/enroll/course/{course.slug}/"
        else:
            records = RatingFactory.create_batch(21, course=course)
            url = "/api/v1/rating/instructor/"

    first = client.get(url)
    assert first.status_code == 200, first.data
    assert set(first.data) == {"count", "next", "previous", "results"}
    assert first.data["count"] == 21
    assert len(first.data["results"]) == 20
    assert first.data["previous"] is None
    assert "page=2" in first.data["next"]

    second = client.get(first.data["next"])
    assert second.status_code == 200, second.data
    assert second.data["count"] == 21
    assert len(second.data["results"]) == 1
    assert second.data["next"] is None
    assert second.data["previous"] is not None
    ids = [str(row["id"]) for row in first.data["results"] + second.data["results"]]
    assert len(set(ids)) == 21
    assert set(ids) == {str(record.pk) for record in records}
    assert client.get(second.data["previous"]).data["results"] == first.data["results"]
    assert client.get(url, {"page": 3}).status_code == 404
    assert client.get(url, {"page": "invalid"}).status_code == 404
