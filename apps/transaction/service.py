from apps.core.email_notifications import queue_notification_email

from .repository import TransactionRepository


class TransactionService:
    """
    Service to handle business logic for Transaction.
    """

    @staticmethod
    def get_transaction_queryset():
        return TransactionRepository.get_transaction_queryset()

    @staticmethod
    def get_user_transactions(user):
        return TransactionRepository.get_user_transactions(user)

    @staticmethod
    def get_admin_transactions():
        return TransactionRepository.get_admin_transactions()

    @staticmethod
    def get_instructor_transactions(user):
        return TransactionRepository.get_instructor_transactions(user)

    @staticmethod
    def create_transaction(
        user,
        amount,
        transaction_type,
        status="pending",
        wallet=None,
        description=None,
        tx_id=None,
    ):
        """
        Creates a new transaction.
        """
        return TransactionRepository.create_transaction(
            user=user,
            amount=amount,
            transaction_type=transaction_type,
            status=status,
            wallet=wallet,
            description=description,
            tx_id=tx_id,
        )

    @staticmethod
    def update_transaction_status(transaction, status):
        """Updates the status of a transaction."""
        previous_status = transaction.status
        transaction = TransactionRepository.update_transaction(
            transaction, status=status
        )
        if previous_status != transaction.status:
            queue_notification_email(
                transaction.user,
                subject=f"Payment status: {transaction.status}",
                title=f"Payment {transaction.status}",
                message=(
                    f"Your transaction for INR {transaction.amount} is now "
                    f"{transaction.status}. {transaction.description or ''}"
                ),
                preference_required=False,
            )
        return transaction
