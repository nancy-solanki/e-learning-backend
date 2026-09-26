import pytest

from apps.category.service import CategoryService


@pytest.mark.parametrize("value", [None, [], ()])
def test_missing_thumbnail(value, mocker):
    upload = mocker.patch("apps.category.service.FileService.upload_file_to_cloud")
    with pytest.raises(ValueError, match="Thumbnail is required"):
        CategoryService.upload_thumbnail(value)
    upload.assert_not_called()


@pytest.mark.parametrize("container", [lambda f: f, lambda f: [f], lambda f: (f,)])
def test_upload_thumbnail(container, upload, cloud_upload):
    result = CategoryService.upload_thumbnail(container(upload))
    cloud_upload.assert_called_once_with(upload, "category")
    assert result.pk


@pytest.mark.django_db
def test_update_preserves_input(category, upload, cloud_upload):
    data = {"description": "Updated"}
    updated = CategoryService.update_category(category, data, thumbnail=upload)
    assert data == {"description": "Updated"}
    updated.refresh_from_db()
    assert updated.description == "Updated"
    assert updated.thumbnail.name == "image.png"


@pytest.mark.django_db
def test_update_without_thumbnail(category):
    thumbnail_id = category.thumbnail_id
    CategoryService.update_category(category, {"description": "Updated"})
    category.refresh_from_db()
    assert category.thumbnail_id == thumbnail_id
    assert category.description == "Updated"


@pytest.mark.django_db
def test_delete_and_queryset(category):
    CategoryService.delete_category(category)
    category.refresh_from_db()
    assert category.deleted_at is not None
    assert not CategoryService.get_queryset_for_user(category.user).exists()
