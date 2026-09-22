from .models import Bank

class BankRepository:
    """
    Repository to handle database interactions relating to the Bank model.
    """

    @staticmethod
    def get_bank_by_id(bank_id):
        return Bank.objects.filter(id=bank_id, deleted_at__isnull=True).first()

    @staticmethod
    def get_banks_by_user(user):
        return Bank.objects.filter(user=user, deleted_at__isnull=True)

    @staticmethod
    def get_default_bank(user):
        return Bank.objects.filter(user=user, default=True, deleted_at__isnull=True).first()

    @staticmethod
    def create_bank(user, **validated_data):
        # If this is the first bank for the user, set it as default
        has_bank = Bank.objects.filter(user=user).exists()
        default = not has_bank
        
        bank = Bank.objects.create(user=user, default=default, **validated_data)
        return bank

    @staticmethod
    def save(bank):
        bank.save()
        return bank

    @staticmethod
    def get_all_banks():
        return Bank.objects.filter(deleted_at__isnull=True)
