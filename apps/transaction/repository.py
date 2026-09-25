from .models import Transaction


class TransactionRepository:
    """
    Repository to handle database interactions for Transaction.
    """

    @staticmethod
    def get_transaction_queryset():
        return Transaction.objects.filter(deleted_at__isnull=True)

    @staticmethod
    def get_user_transactions(user):
        return TransactionRepository.get_transaction_queryset().filter(user=user)

    @staticmethod
    def get_transaction_by_id(transaction_id):
        return (
            TransactionRepository.get_transaction_queryset()
            .filter(id=transaction_id)
            .first()
        )

    @staticmethod
    def create_transaction(**kwargs):
        return Transaction.objects.create(**kwargs)

    @staticmethod
    def update_transaction(transaction, **kwargs):
        for field, value in kwargs.items():
            setattr(transaction, field, value)
        transaction.save()
        return transaction

    @staticmethod
    def soft_delete_transaction(transaction):
        return transaction.soft_delete()

    @staticmethod
    def restore_transaction(transaction):
        return transaction.restore()

    @staticmethod
    def toggle_transaction_status(transaction):
        return transaction.toggle_deleted()
