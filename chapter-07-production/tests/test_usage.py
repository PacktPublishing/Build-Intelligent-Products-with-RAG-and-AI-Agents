import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from usage import (
    UsageDecision,
    UsageError,
    consume_daily_request,
)


class UsageTests(unittest.TestCase):
    def test_allowed_response_is_parsed(self):
        client = MagicMock()
        client.rpc.return_value.execute.return_value = (
            SimpleNamespace(
                data=[
                    {
                        "allowed": True,
                        "used_count": 1,
                        "daily_limit": 3,
                        "remaining_count": 2,
                    }
                ]
            )
        )

        result = consume_daily_request(client)

        self.assertEqual(
            result,
            UsageDecision(
                allowed=True,
                used_count=1,
                daily_limit=3,
                remaining_count=2,
            ),
        )
        client.rpc.assert_called_once_with(
            "consume_daily_request"
        )

    def test_denied_response_is_parsed(self):
        client = MagicMock()
        client.rpc.return_value.execute.return_value = (
            SimpleNamespace(
                data=[
                    {
                        "allowed": False,
                        "used_count": 3,
                        "daily_limit": 3,
                        "remaining_count": 0,
                    }
                ]
            )
        )

        result = consume_daily_request(client)

        self.assertFalse(result.allowed)
        self.assertEqual(result.remaining_count, 0)

    def test_provider_error_becomes_usage_error(self):
        client = MagicMock()
        client.rpc.return_value.execute.side_effect = RuntimeError(
            "database unavailable"
        )

        with self.assertLogs("usage", level="ERROR"):
            with self.assertRaisesRegex(
                UsageError,
                "could not verify",
            ):
                consume_daily_request(client)

    def test_malformed_response_is_rejected(self):
        client = MagicMock()
        client.rpc.return_value.execute.return_value = (
            SimpleNamespace(data=[])
        )

        with self.assertRaisesRegex(
            UsageError,
            "unexpected usage response",
        ):
            consume_daily_request(client)


if __name__ == "__main__":
    unittest.main()