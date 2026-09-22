from django.utils import timezone

from .models import Category


class CategoryRepository:
    """
    Repository to handle database interactions for Category.
    """

    @staticmethod
    def get_category_by_slug(slug):
        return Category.objects.filter(slug=slug).first()

    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    @staticmethod
    def get_active_categories():
        return Category.objects.filter(deleted_at__isnull=True)

    @staticmethod
    def create_category(**kwargs):
        return Category.objects.create(**kwargs)

    @staticmethod
    def update_category(category, **kwargs):
        for field, value in kwargs.items():
            setattr(category, field, value)
        category.save()
        return category

    @staticmethod
    def soft_delete_category(category):
        category.deleted_at = timezone.now()
        category.save()
        return category