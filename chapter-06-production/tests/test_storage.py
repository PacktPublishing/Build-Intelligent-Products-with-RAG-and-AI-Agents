import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from config import PROMPT_VERSION, ROAST_MODEL
from storage import StorageError, get_roasts, save_roast


class StorageTests(unittest.TestCase):
    def test_get_roasts_filters_by_user_and_orders_history(self):
        client = MagicMock()

        table_query = client.table.return_value
        select_query = table_query.select.return_value
        filter_query = select_query.eq.return_value
        order_query = filter_query.order.return_value

        expected = [
            {
                "id": "roast-1",
                "created_at": "2026-08-19T10:00:00+00:00",
                "user_intent": "Python engineer",
                "score": 8,
                "roast_text": "SCORE: 8/10",
                "prompt_version": PROMPT_VERSION,
                "model_name": ROAST_MODEL,
            }
        ]

        order_query.execute.return_value = SimpleNamespace(
            data=expected
        )

        result = get_roasts(client, "user-123")

        self.assertEqual(result, expected)
        client.table.assert_called_once_with("roasts")
        select_query.eq.assert_called_once_with(
            "user_id",
            "user-123",
        )
        filter_query.order.assert_called_once_with("created_at")

    def test_save_roast_inserts_authenticated_record(self):
        client = MagicMock()

        save_roast(
            client,
            "user-123",
            " Python engineer ",
            "8",
            " SCORE: 8/10\nGood resume. ",
        )

        inserted_payload = (
            client.table.return_value.insert.call_args.args[0]
        )

        self.assertEqual(
            inserted_payload,
            {
                "user_id": "user-123",
                "user_intent": "Python engineer",
                "score": 8,
                "roast_text": "SCORE: 8/10\nGood resume.",
                "prompt_version": PROMPT_VERSION,
                "model_name": ROAST_MODEL,
            },
        )

        (
            client.table.return_value
            .insert.return_value
            .execute.assert_called_once_with()
        )

    def test_database_failures_become_storage_errors(self):
        client = MagicMock()
        client.table.side_effect = RuntimeError(
            "database unavailable"
        )

        with self.assertRaisesRegex(
            StorageError,
            "history could not be loaded",
        ):
            get_roasts(client, "user-123")


if __name__ == "__main__":
    unittest.main()