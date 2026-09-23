from .models import Wallet


class WalletRepository:
    """
    Repository to handle database interactions for Wallet.
    """

    @staticmethod
    def get_wallet_queryset_by_user(user):
        return Wallet.objects.filter(user=user, deleted_at__isnull=True)

    @staticmethod
    def get_wallet_by_user(user):
        return WalletRepository.get_wallet_queryset_by_user(user).first()

    @staticmethod
    def get_site_wallet():
        return Wallet.objects.filter(is_site_wallet=True, deleted_at__isnull=True).first()

    @staticmethod
    def create_wallet(**kwargs):
        return Wallet.objects.create(**kwargs)

    @staticmethod
    def update_wallet(wallet, **kwargs):
        for field, value in kwargs.items():
            setattr(wallet, field, value)
        wallet.save()
        return wallet

    @staticmethod
    def soft_delete_wallet(wallet):
        return wallet.soft_delete()

    @staticmethod
    def restore_wallet(wallet):
        return wallet.restore()

    @staticmethod
    def toggle_wallet_status(wallet):
        return wallet.toggle_deleted()
