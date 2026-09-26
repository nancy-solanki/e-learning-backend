import pytest

from apps.category.tests.factories import CategoryFactory
from apps.common.tests.factories import FileFactory
from apps.course.service import CourseService

pytestmark = pytest.mark.django_db


def test_create_update_toggle_and_queries(instructor):
    course = CourseService.create_course(
        title="Python", instructor=instructor, thumbnail=FileFactory()
    )
    assert CourseService.update_course(course, status="published") == course
    category = CategoryFactory()
    course.categories.add(category)
    assert list(CourseService.get_public_queryset()) == [course]
    assert list(CourseService.get_queryset_for_user(instructor)) == [course]
    assert list(CourseService.get_courses_by_category(category)) == [course]
    CourseService.toggle_course_status(course)
    course.refresh_from_db()
    assert course.is_deleted
