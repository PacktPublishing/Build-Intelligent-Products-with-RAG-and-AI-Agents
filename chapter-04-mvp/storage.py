"""The data layer: four small functions over two CSVs.

app.py (and anything else in this chapter) only ever touches data
through save_user, save_roast, get_roasts, and ensure_storage. When a
later chapter swaps CSV for a real database, this file's internals get
rewritten and these four signatures don't move.

Concurrent writes and ephemeral hosting storage are known, intentional
limitations of this chapter's data layer -- see the chapter README's
"Known limitations" section.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

import config

USERS_COLUMNS = ["email", "created_at"]
ROASTS_COLUMNS = ["email", "created_at", "target_role", "score", "roast_text"]


def _data_dir() -> Path:
    """Read config.DATA_DIR at call time, not at import time.

    Reading it fresh on every call (instead of caching a Path at import
    time) is what lets a caller point storage at a different directory
    just by setting ``config.DATA_DIR`` first -- useful for anything
    that shouldn't touch the real data/ folder.
    """
    return Path(config.DATA_DIR)


def _users_path() -> Path:
    return _data_dir() / "users.csv"


def _roasts_path() -> Path:
    return _data_dir() / "roasts.csv"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_storage() -> None:
    """Create the data directory and both CSV files with headers, if needed."""
    _data_dir().mkdir(parents=True, exist_ok=True)
    for path, header in [
        (_users_path(), USERS_COLUMNS),
        (_roasts_path(), ROASTS_COLUMNS),
    ]:
        if not path.exists():
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)


def save_user(email: str) -> None:
    """Record a user's first visit. Does nothing if the user already exists."""
    ensure_storage()
    email = _normalize_email(email)

    with open(_users_path(), newline="", encoding="utf-8") as f:
        if any(row["email"] == email for row in csv.DictReader(f)):
            return

    with open(_users_path(), "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([email, _now()])


def save_roast(email: str, target_role: str, score: str, roast_text: str) -> None:
    """Append one roast record for the given user."""
    ensure_storage()
    email = _normalize_email(email)

    with open(_roasts_path(), "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([email, _now(), target_role, score, roast_text])


def get_roasts(email: str) -> list[dict[str, str]]:
    """Return every roast saved for the given user, oldest first."""
    ensure_storage()
    email = _normalize_email(email)

    with open(_roasts_path(), newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row["email"] == email]
