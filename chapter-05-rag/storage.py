"""CSV persistence boundary retained from the Chapter 4 MVP."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import config

USERS_COLUMNS = ["email", "created_at"]
ROASTS_COLUMNS = ["email", "created_at", "target_role", "score", "roast_text", "evidence_ids"]


def _data_dir() -> Path:
    return Path(config.DATA_DIR)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_storage() -> None:
    _data_dir().mkdir(parents=True, exist_ok=True)
    for name, columns in [("users.csv", USERS_COLUMNS), ("roasts.csv", ROASTS_COLUMNS)]:
        path = _data_dir() / name
        if not path.exists():
            with path.open("w", newline="", encoding="utf-8") as file:
                csv.writer(file).writerow(columns)


def save_user(email: str) -> None:
    ensure_storage()
    email = email.strip().lower()
    path = _data_dir() / "users.csv"
    with path.open(newline="", encoding="utf-8") as file:
        if any(row["email"] == email for row in csv.DictReader(file)):
            return
    with path.open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow([email, _now()])


def save_roast(email: str, target_role: str, score: str, roast_text: str, evidence_ids: str) -> None:
    ensure_storage()
    with (_data_dir() / "roasts.csv").open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow([email.strip().lower(), _now(), target_role, score, roast_text, evidence_ids])


def get_roasts(email: str) -> list[dict[str, str]]:
    ensure_storage()
    with (_data_dir() / "roasts.csv").open(newline="", encoding="utf-8") as file:
        return [row for row in csv.DictReader(file) if row["email"] == email.strip().lower()]
