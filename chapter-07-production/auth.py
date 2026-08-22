"""Supabase password authentication for ResumeRoast."""

from dataclasses import dataclass
from typing import Callable, TypeVar

from supabase import Client, create_client


MIN_PASSWORD_CHARS = 8

T = TypeVar("T")


class AuthError(RuntimeError):
    """A safe authentication error that the Streamlit UI can display."""


@dataclass(frozen=True)
class SignedInUser:
    """The small amount of identity data required by the application."""

    id: str
    email: str


def create_supabase_client(url: str, key: str) -> Client:
    """Create one Supabase client for one Streamlit user session."""

    if not url or not url.strip():
        raise AuthError("SUPABASE_URL is missing.")

    if not key or not key.strip():
        raise AuthError("SUPABASE_KEY is missing.")

    return create_client(url.strip(), key.strip())


def _validate_credentials(email: str, password: str) -> tuple[str, str]:
    normalized_email = email.strip().lower()

    if "@" not in normalized_email or "." not in normalized_email:
        raise AuthError("Enter a valid email address.")

    if len(password) < MIN_PASSWORD_CHARS:
        raise AuthError(
            f"Your password must contain at least {MIN_PASSWORD_CHARS} characters."
        )

    return normalized_email, password


def _run_auth_action(action: str, operation: Callable[[], T]) -> T:
    """Convert provider exceptions into errors understood by the UI."""

    try:
        return operation()
    except Exception as exc:
        detail = str(exc).strip()
        raise AuthError(detail or f"{action} failed. Please try again.") from exc


def _require_session(response, action: str) -> SignedInUser:
    """Ensure that Supabase returned a signed-in user and session."""

    user = getattr(response, "user", None)
    session = getattr(response, "session", None)

    if user is None or session is None:
        raise AuthError(
            f"{action} did not create a session. "
            "Check that Confirm email is disabled in Supabase."
        )

    user_id = getattr(user, "id", None)
    email = getattr(user, "email", None)

    if not user_id or not email:
        raise AuthError(f"{action} returned incomplete user information.")

    return SignedInUser(id=str(user_id), email=email.lower())


def sign_up(client: Client, email: str, password: str) -> SignedInUser:
    """Create a user and immediately authenticate them."""

    normalized_email, validated_password = _validate_credentials(email, password)

    response = _run_auth_action(
        "Sign-up",
        lambda: client.auth.sign_up(
            {
                "email": normalized_email,
                "password": validated_password,
            }
        ),
    )

    return _require_session(response, "Sign-up")


def sign_in(client: Client, email: str, password: str) -> SignedInUser:
    """Authenticate an existing user."""

    normalized_email, validated_password = _validate_credentials(email, password)

    response = _run_auth_action(
        "Sign-in",
        lambda: client.auth.sign_in_with_password(
            {
                "email": normalized_email,
                "password": validated_password,
            }
        ),
    )

    return _require_session(response, "Sign-in")


def sign_out(client: Client) -> None:
    """Revoke the current Supabase refresh token."""

    _run_auth_action("Sign-out", client.auth.sign_out)