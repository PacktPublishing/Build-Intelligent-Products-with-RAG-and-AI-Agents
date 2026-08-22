"""Per-user daily request limits enforced by Supabase."""

from dataclasses import dataclass
import logging

from supabase import Client


logger = logging.getLogger(__name__)


class UsageError(RuntimeError):
    """A safe usage-limit error that the UI can display."""


@dataclass(frozen=True)
class UsageDecision:
    """The result returned by the atomic database function."""

    allowed: bool
    used_count: int
    daily_limit: int
    remaining_count: int


def consume_daily_request(client: Client) -> UsageDecision:
    """Atomically reserve one request from today's allowance."""

    try:
        response = (
            client.rpc("consume_daily_request")
            .execute()
        )
    except Exception as exc:
        logger.exception("Daily usage RPC failed")
        raise UsageError(
            "We could not verify your daily usage. "
            "Please try again in a moment."
        ) from exc

    data = response.data

    if isinstance(data, dict):
        row = data
    elif (
        isinstance(data, list)
        and len(data) == 1
        and isinstance(data[0], dict)
    ):
        row = data[0]
    else:
        raise UsageError(
            "Supabase returned an unexpected usage response."
        )

    try:
        allowed = row["allowed"]
        used_count = int(row["used_count"])
        daily_limit = int(row["daily_limit"])
        remaining_count = int(row["remaining_count"])
    except (KeyError, TypeError, ValueError) as exc:
        raise UsageError(
            "Supabase returned incomplete usage information."
        ) from exc

    if not isinstance(allowed, bool):
        raise UsageError(
            "Supabase returned an invalid usage decision."
        )

    if (
        used_count < 0
        or daily_limit < 1
        or remaining_count < 0
    ):
        raise UsageError(
            "Supabase returned invalid usage counts."
        )

    return UsageDecision(
        allowed=allowed,
        used_count=used_count,
        daily_limit=daily_limit,
        remaining_count=remaining_count,
    )