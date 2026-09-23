from .repository import WalletRepository


class WalletService:
    """
    Service to handle business logic for Wallet.
    """

    @staticmethod
    def get_wallet_queryset_by_user(user):
        return WalletRepository.get_wallet_queryset_by_user(user)

    @staticmethod
    def get_wallet_by_user(user):
        return WalletRepository.get_wallet_by_user(user)

    @staticmethod
    def get_site_wallet():
        return WalletRepository.get_site_wallet()

    @staticmethod
    def toggle_wallet_status(wallet):
        """
        Toggles the soft delete status of a wallet.
        """
        return WalletRepository.toggle_wallet_status(wallet)

    @staticmethod
    def delete_wallet(wallet):
        """
        Soft deletes a wallet.
        """
        return WalletRepository.soft_delete_wallet(wallet)

    @staticmethod
    def restore_wallet(wallet):
        """
        Restores a soft-deleted wallet.
        """
        return WalletRepository.restore_wallet(wallet)
