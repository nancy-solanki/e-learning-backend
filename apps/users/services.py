class UserService:
    """
    Service to handle business logic relating to the User model.
    """

    @staticmethod
    def make_instructor(user) -> str:
        """
        Grants a user the instructor role.
        """
        user.become_instructor()
        return "User updated successfully"

    @staticmethod
    def toggle_admin(user) -> str:
        """
        Toggles admin privileges for a user.
        """
        action_taken = user.toggle_admin_privileges()
        group_name = "admin"
        return f"User {action_taken} {group_name} group successfully"

    @staticmethod
    def toggle_status(user) -> str:
        """
        Activates or suspends a user's account.
        """
        action = user.toggle_status()
        return f"User {action} successfully"
