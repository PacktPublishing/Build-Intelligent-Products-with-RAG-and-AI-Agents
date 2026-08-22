"""Authenticated Supabase storage for ResumeRoast.

Resume contents are never stored. Only the generated roast, score,
target intent, model metadata, and authenticated user ID are saved.
"""
import logging
from supabase import Client

from config import PROMPT_VERSION, ROAST_MODEL

logger = logging.getLogger(__name__)
class StorageError(RuntimeError):
    """A safe database error that the Streamlit UI can display."""


def save_roast(
    client: Client,
    user_id: str,
    user_intent: str,
    score: str,
    roast_text: str,
) -> None:
    """Save one roast belonging to the authenticated user."""

    try:
        numeric_score = int(score)
    except (TypeError, ValueError) as exc:
        raise StorageError("The roast score could not be saved.") from exc

    if not 0 <= numeric_score <= 10:
        raise StorageError("The roast score is outside the allowed range.")

    payload = {
        "user_id": str(user_id),
        "user_intent": user_intent.strip(),
        "score": numeric_score,
        "roast_text": roast_text.strip(),
        "prompt_version": PROMPT_VERSION,
        "model_name": ROAST_MODEL,
    }
    logger.info(
    "Saving roast with client type=%s",
    type(client).__name__,
    )
    try:
        client.table("roasts").insert(payload).execute()
    except Exception as exc:
        logger.error(
            "Supabase roast insert failed; client type=%s",
            type(client).__name__,
        )
        raise StorageError(
            "Your roast was generated, but it could not be saved. "
            "Please try again."
        ) from exc


def get_roasts(
    client: Client,
    user_id: str,
) -> list[dict]:
    """Return the authenticated user's roasts, oldest first."""

    try:
        response = (
            client.table("roasts")
            .select(
                "id, created_at, user_intent, score, "
                "roast_text, prompt_version, model_name"
            )
            .eq("user_id", str(user_id))
            .order("created_at")
            .execute()
        )
    except Exception as exc:
        raise StorageError(
            "Your roast history could not be loaded. "
            "Please try again."
        ) from exc

    return list(response.data or [])