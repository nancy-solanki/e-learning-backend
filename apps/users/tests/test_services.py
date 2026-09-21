from unittest.mock import MagicMock

from apps.users.services import UserService


class TestUserService:
    """Tests for UserService business logic (no DB required)."""

    def test_make_instructor_calls_become_instructor(self):
        user = MagicMock()
        result = UserService.make_instructor(user)
        user.become_instructor.assert_called_once()
        assert result == "User updated successfully"

    def test_toggle_admin_added(self):
        user = MagicMock()
        user.toggle_admin_privileges.return_value = "added to"
        result = UserService.toggle_admin(user)
        assert result == "User added to admin group successfully"

    def test_toggle_admin_removed(self):
        user = MagicMock()
        user.toggle_admin_privileges.return_value = "removed from"
        result = UserService.toggle_admin(user)
        assert result == "User removed from admin group successfully"

    def test_toggle_status_active(self):
        user = MagicMock()
        user.toggle_status.return_value = "activated"
        result = UserService.toggle_status(user)
        assert result == "User activated successfully"

    def test_toggle_status_suspended(self):
        user = MagicMock()
        user.toggle_status.return_value = "suspended"
        result = UserService.toggle_status(user)
        assert result == "User suspended successfully"
