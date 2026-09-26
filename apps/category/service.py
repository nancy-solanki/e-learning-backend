from apps.common.service import FileService

from .repository import CategoryRepository


class CategoryService:
    """
    Service to handle business logic for Category.
    """

    @staticmethod
    def _resolve_thumbnail(thumbnail):
        if isinstance(thumbnail, (list, tuple)):
            return thumbnail[0] if thumbnail else None
        return thumbnail

    @staticmethod
    def get_queryset_for_user(user):
        return CategoryRepository.get_active_categories()

    @staticmethod
    def upload_thumbnail(thumbnail):
        file_obj = CategoryService._resolve_thumbnail(thumbnail)
        if not file_obj:
            raise ValueError("Thumbnail is required.")
        return FileService.upload_file_to_cloud(file_obj, "category")

    @staticmethod
    def update_category(category, data, thumbnail=None):
        data = data.copy()
        if thumbnail is not None:
            data["thumbnail"] = CategoryService.upload_thumbnail(thumbnail)
        return CategoryRepository.update_category(category, **data)

    @staticmethod
    def delete_category(category):
        return CategoryRepository.soft_delete_category(category)
