from .repository import BankRepository
from rest_framework.exceptions import ValidationError

class BankService:
    """
    Service to handle business logic relating to the Bank model.
    """

    @staticmethod
    def set_default_bank(user, bank_id) -> str:
        """
        Sets a specific bank as the default for a user.
        """
        bank = BankRepository.get_bank_by_id(bank_id)
        if not bank or bank.user != user:
            raise ValidationError("Bank not found or not owned by user.")

        # Unset current default
        current_default = BankRepository.get_default_bank(user)
        if current_default:
            current_default.default = False
            BankRepository.save(current_default)

        # Set new default
        bank.default = True
        BankRepository.save(bank)
        return "Account set successfully"

    @staticmethod
    def toggle_delete_bank(bank) -> str:
        """
        Toggles the deleted status of a bank.
        """
        if bank.default and not bank.is_deleted:
            raise ValidationError("Primary Account can't be deleted")

        action = bank.toggle_deleted()
        if action == "activated" or not bank.is_deleted:
             return "Activated successfully"
        return "Deleted successfully"
