import pytest
from django.db import IntegrityError, transaction

from apps.category.repository import CategoryRepository

pytestmark = pytest.mark.django_db


def test_title_slug_and_stable_url(category_factory):
    category = category_factory(title="Python Basics")
    assert category.title == "python basics"
    assert category.slug == "python-basics"
    assert str(category) == "python basics"
    category.title = "New Title"
    category.save()
    category.refresh_from_db()
    assert category.slug == "python-basics"


def test_custom_slug(category_factory):
    assert category_factory(slug="custom").slug == "custom"


@pytest.mark.parametrize("field", ["title", "slug", "thumbnail"])
def test_database_uniqueness(category, category_factory, field):
    with pytest.raises(IntegrityError), transaction.atomic():
        category_factory(**{field: getattr(category, field)})


def test_repository_lookup_and_soft_delete(category):
    assert CategoryRepository.get_category_by_slug(category.slug) == category
    assert CategoryRepository.get_category_by_slug("missing") is None
    CategoryRepository.soft_delete_category(category)
    assert category in CategoryRepository.get_all_categories()
    assert category not in CategoryRepository.get_active_categories()


def test_repository_create(category, file_factory):
    created = CategoryRepository.create_category(
        title="New", description="Learn", user=category.user, thumbnail=file_factory()
    )
    assert CategoryRepository.get_category_by_slug("new") == created
