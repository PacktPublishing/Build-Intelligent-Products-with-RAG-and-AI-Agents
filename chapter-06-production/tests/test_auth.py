import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from auth import (
    AuthError,
    SignedInUser,
    create_supabase_client,
    sign_in,
    sign_out,
    sign_up,
)


class AuthTests(unittest.TestCase):
    @staticmethod
    def successful_response(
        user_id="user-123",
        email="reader@example.com",
    ):
        return SimpleNamespace(
            user=SimpleNamespace(id=user_id, email=email),
            session=object(),
        )

    def test_missing_configuration_is_rejected(self):
        with self.assertRaisesRegex(AuthError, "SUPABASE_URL"):
            create_supabase_client("", "public-key")

        with self.assertRaisesRegex(AuthError, "SUPABASE_KEY"):
            create_supabase_client("https://example.supabase.co", "")

    def test_sign_up_returns_user_and_normalizes_email(self):
        client = MagicMock()
        client.auth.sign_up.return_value = self.successful_response()

        user = sign_up(client, " Reader@Example.com ", "securepass")

        self.assertEqual(
            user,
            SignedInUser(id="user-123", email="reader@example.com"),
        )
        client.auth.sign_up.assert_called_once_with(
            {
                "email": "reader@example.com",
                "password": "securepass",
            }
        )

    def test_short_password_is_rejected_before_request(self):
        client = MagicMock()

        with self.assertRaisesRegex(AuthError, "at least 8"):
            sign_up(client, "reader@example.com", "short")

        client.auth.sign_up.assert_not_called()

    def test_sign_up_requires_an_immediate_session(self):
        client = MagicMock()
        client.auth.sign_up.return_value = SimpleNamespace(
            user=SimpleNamespace(
                id="user-123",
                email="reader@example.com",
            ),
            session=None,
        )

        with self.assertRaisesRegex(AuthError, "Confirm email"):
            sign_up(client, "reader@example.com", "securepass")

    def test_sign_in_returns_authenticated_user(self):
        client = MagicMock()
        client.auth.sign_in_with_password.return_value = (
            self.successful_response()
        )

        user = sign_in(client, "reader@example.com", "securepass")

        self.assertEqual(user.id, "user-123")
        self.assertEqual(user.email, "reader@example.com")

    def test_provider_errors_become_auth_errors(self):
        client = MagicMock()
        client.auth.sign_in_with_password.side_effect = RuntimeError(
            "Invalid login credentials"
        )

        with self.assertRaisesRegex(AuthError, "Invalid login credentials"):
            sign_in(client, "reader@example.com", "incorrect-password")

    def test_sign_out_uses_supabase_auth(self):
        client = MagicMock()

        sign_out(client)

        client.auth.sign_out.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()