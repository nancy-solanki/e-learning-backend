from .repository import LocalizationRepository


class LocalizationService:
    """
    Service to handle business logic for Localization.
    """

    @staticmethod
    def get_queryset_for_user(user):
        if user.is_superuser or getattr(user, 'is_admin', False):
            return LocalizationRepository.get_all_localizations()
        return LocalizationRepository.get_active_localizations()

    @staticmethod
    def toggle_localization_status(localization):
        if localization.is_deleted:
            return LocalizationRepository.restore_localization(localization)
        return LocalizationRepository.soft_delete_localization(localization)
