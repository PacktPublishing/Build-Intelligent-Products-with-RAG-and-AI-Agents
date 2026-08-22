"""Every number and model name you might ever change, in one place.

Nothing else in this chapter should hardcode a model name or a limit.
When a provider renames or reprices a model, or the cost budget needs
to move, this is the only file that changes.
"""

from pathlib import Path

# Model names below are the ones current in the book's manuscript at the
# time of writing. Providers rename, deprecate, and reprice models on
# their own schedule -- treat these as examples to verify against your
# provider's current documentation before you build, not as permanently
# correct values. Changing a model tier is a one-line edit here.
ROAST_MODEL = "gpt-5"  # frontier tier: the roast itself
CHECK_MODEL = "gpt-5-mini"  # budget tier: input checking
EMBEDDING_MODEL = "text-embedding-3-small"

# ROAST_MODEL is a reasoning model: it spends part of MAX_OUTPUT_TOKENS on
# hidden reasoning before writing the visible critique. Left at the
# provider's default reasoning effort, a long, detailed prompt like
# ROAST_SYSTEM_PROMPT can consume the entire output budget on reasoning
# and return an empty response. "low" leaves enough budget for the
# critique itself; raise MAX_OUTPUT_TOKENS instead of lowering this if a
# future prompt needs more headroom.
#
# If you swap ROAST_MODEL for a non-reasoning model (e.g. gpt-4o-mini),
# set this to None -- non-reasoning models reject the "reasoning"
# parameter entirely, and roast.py only sends it when this is truthy.
ROAST_REASONING_EFFORT = "low"

MAX_PAGES = 4  # resumes longer than this get rejected
MIN_CHARS = 300  # extracted text shorter than this is treated as empty/scanned
MAX_CHARS = 15000  # hard cap on text sent to the model
MAX_OUTPUT_TOKENS = 1600  # hard cap on what the model sends back

# Chapter 5 adds a loop and network tools. Both are bounded here so the
# agent cannot turn one user action into an unlimited bill or an
# unlimited network request.
MAX_AGENT_STEPS = 3
MAX_INTENT_CHARS = 1000
MAX_RETRIEVED_CHUNKS = 3
MAX_EVIDENCE_CHARS = 4_500
MIN_RETRIEVAL_SCORE = 0.35
TOOL_TIMEOUT_SECONDS = 10
MAX_TOOL_REDIRECTS = 3

CHAPTER_ROOT = Path(__file__).resolve().parent
DATA_DIR = CHAPTER_ROOT / "data"
CORPUS_PATH = DATA_DIR / "rubrics.json"

PROMPT_VERSION = "v3-rag-agent-production"
