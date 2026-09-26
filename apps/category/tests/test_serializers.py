import pytest

from apps.category.serializers import CategorySerializer

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("title", ["", "   ", "x" * 256])
def test_invalid_title(title):
    serializer = CategorySerializer(data={"title": title, "description": "Learning"})
    assert not serializer.is_valid()
    assert "title" in serializer.errors


@pytest.mark.parametrize("payload", [{}, {"title": "Python"}, {"description": "Learn"}])
def test_required_fields(payload):
    assert not CategorySerializer(data=payload).is_valid()


def test_partial_update_without_title(category):
    serializer = CategorySerializer(
        category, data={"description": "Updated"}, partial=True
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()
    category.refresh_from_db()
    assert category.description == "Updated"


def test_normalizes_title():
    serializer = CategorySerializer(
        data={"title": "  PYTHON  ", "description": "Learn"}
    )
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["title"] == "python"
    assert serializer.validated_data["slug"] == "python"


def test_case_insensitive_duplicate(category_factory):
    category_factory(title="Python")
    serializer = CategorySerializer(data={"title": "PYTHON", "description": "Learn"})
    assert not serializer.is_valid()
    assert "title" in serializer.errors


def test_substring_is_not_duplicate(category_factory):
    category_factory(title="Advanced Python")
    serializer = CategorySerializer(data={"title": "Python", "description": "Learn"})
    assert serializer.is_valid(), serializer.errors


def test_unchanged_title_is_valid(category):
    serializer = CategorySerializer(
        category, data={"title": category.title}, partial=True
    )
    assert serializer.is_valid(), serializer.errors


@pytest.mark.parametrize("title", ["!!!", "x" * 51])
def test_invalid_generated_slug(title):
    serializer = CategorySerializer(data={"title": title, "description": "Learn"})
    assert not serializer.is_valid()
    assert "slug" in serializer.errors


def test_generated_slug_collision(category_factory):
    category_factory(title="Data Science")
    serializer = CategorySerializer(
        data={"title": "Data-Science", "description": "Learn"}
    )
    assert not serializer.is_valid()
    assert "slug" in serializer.errors


def test_protected_fields_and_nested_thumbnail(category):
    serializer = CategorySerializer(
        category,
        data={
            "deleted_at": "2026-01-01T00:00:00Z",
            "created_at": "2020-01-01T00:00:00Z",
        },
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors
    assert "deleted_at" not in serializer.validated_data
    assert "created_at" not in serializer.validated_data
    assert serializer.data["thumbnail"]["url"] == category.thumbnail.url
    assert "user" not in serializer.data
