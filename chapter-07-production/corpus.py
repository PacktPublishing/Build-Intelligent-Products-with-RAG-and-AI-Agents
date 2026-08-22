"""Load the small, curated rubric corpus used by ResumeRoast."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RubricChunk:
    chunk_id: str
    role_family: str
    title: str
    text: str


def load_rubrics(path: Path) -> list[RubricChunk]:
    """Read and validate the local rubric corpus."""
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Rubric corpus not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Rubric corpus is not valid JSON: {path}") from exc

    chunks = []
    for index, record in enumerate(records, start=1):
        required = ("chunk_id", "role_family", "title", "text")
        if not isinstance(record, dict) or any(not record.get(key) for key in required):
            raise ValueError(f"Rubric record {index} is missing a required field.")
        chunks.append(RubricChunk(**{key: str(record[key]) for key in required}))
    return chunks
