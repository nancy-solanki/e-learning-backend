import pytest
from django.utils import timezone

from apps.category.tests.factories import CategoryFactory
from apps.course.repository import CourseRepository
from apps.course.tests.factories import CourseFactory
from apps.users.tests.factories import SuperuserFactory

pytestmark = pytest.mark.django_db


def test_public_visibility_and_category(instructor):
    category = CategoryFactory()
    published = CourseFactory(instructor=instructor, status="published")
    published.categories.add(category)
    CourseFactory(status="draft")
    CourseFactory(status="published", deleted_at=timezone.now())
    CourseFactory(status="published", instructor__status="SA")
    assert list(CourseRepository.get_published_courses()) == [published]
    assert list(CourseRepository.get_courses_by_category(category)) == [published]
    assert not CourseRepository.get_courses_by_category(CategoryFactory()).exists()


def test_user_scoping(course, instructor):
    foreign = CourseFactory()
    deleted = CourseFactory(instructor=instructor, deleted_at=timezone.now())
    assert list(CourseRepository.get_user_courses(instructor)) == [course]
    assert set(CourseRepository.get_user_courses(SuperuserFactory())) == {
        course,
        foreign,
        deleted,
    }
    assert set(CourseRepository.get_all_courses()) == {course, foreign, deleted}


def test_delete_and_restore(course):
    CourseRepository.soft_delete_course(course)
    course.refresh_from_db()
    assert course.is_deleted
    CourseRepository.restore_course(course)
    course.refresh_from_db()
    assert not course.is_deleted
