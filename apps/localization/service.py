from .repository import LocalizationRepository


class LocalizationService:
    """
    Service to handle business logic for Localization.
    """

    @staticmethod
    def get_queryset_for_user(user):
        if user.is_authenticated and user.is_admin:
            return LocalizationRepository.get_all_localizations()
        return LocalizationRepository.get_all_localizations().none()

    @staticmethod
    def toggle_localization_status(localization):
        if localization.is_deleted:
            return LocalizationRepository.restore_localization(localization)
        return LocalizationRepository.soft_delete_localization(localization)
