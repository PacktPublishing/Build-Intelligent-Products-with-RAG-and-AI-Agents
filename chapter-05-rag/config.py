"""Configuration for the Chapter 5 grounded ResumeRoast build."""

from pathlib import Path

ROAST_MODEL = "gpt-5"
CHECK_MODEL = "gpt-5-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
ROAST_REASONING_EFFORT = "low"

MAX_PAGES = 4
MIN_CHARS = 300
MAX_CHARS = 15_000
MAX_OUTPUT_TOKENS = 1_800
MAX_ROLE_CHARS = 100
MAX_RETRIEVED_CHUNKS = 3
MAX_EVIDENCE_CHARS = 4_500
MIN_RETRIEVAL_SCORE = 0.35

DATA_DIR = Path("data")
CORPUS_PATH = Path("data") / "rubrics.json"
PROMPT_VERSION = "v2-rag"
