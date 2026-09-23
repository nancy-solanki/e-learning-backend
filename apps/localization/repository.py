from django.utils import timezone

from .models import Localization


class LocalizationRepository:
    """
    Repository to handle database interactions for Localization.
    """

    @staticmethod
    def get_all_localizations():
        return Localization.objects.all()

    @staticmethod
    def get_active_localizations():
        return Localization.objects.filter(deleted_at__isnull=True)

    @staticmethod
    def create_localization(**kwargs):
        return Localization.objects.create(**kwargs)

    @staticmethod
    def update_localization(localization, **kwargs):
        for field, value in kwargs.items():
            setattr(localization, field, value)
        localization.save()
        return localization

    @staticmethod
    def soft_delete_localization(localization):
        localization.deleted_at = timezone.now()
        localization.save(update_fields=['deleted_at'])
        return localization

    @staticmethod
    def restore_localization(localization):
        localization.deleted_at = None
        localization.save(update_fields=['deleted_at'])
        return localization
