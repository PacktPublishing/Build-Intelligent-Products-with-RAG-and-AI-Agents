"""The core action: resume text in, roast out.

This module never talks to Streamlit and never creates a paid API
client on import -- that's what lets it run from a plain terminal
script (scripts/run_core_action.py) with no Streamlit dependency at all.
"""

import re

from openai import OpenAI, OpenAIError

from config import CHECK_MODEL, MAX_OUTPUT_TOKENS, ROAST_MODEL, ROAST_REASONING_EFFORT
from prompts import ROAST_SYSTEM_PROMPT

CHECK_PROMPT = (
    "You check whether a document is a resume or CV. "
    "Reply with exactly one word: YES or NO."
)

# Only a bounded prefix of the document is sent to the budget-tier
# check -- enough to tell whether it's a resume, far short of MAX_CHARS.
CHECK_TEXT_PREFIX_CHARS = 3000

_SCORE_LINE = re.compile(r"^SCORE:\s*(\d{1,2})\s*/\s*10\s*$")


class RoastError(Exception):
    """Raised with a user-facing message when the model API can't be used."""


def create_client(api_key: str) -> OpenAI:
    """Build an OpenAI client from an explicit key.

    Kept separate from module import so callers control exactly when
    (and whether) a client -- and therefore a provider connection --
    gets created.
    """
    return OpenAI(api_key=api_key)


def is_resume(client: OpenAI, text: str) -> bool:
    """Budget-tier gate: is this document actually a resume?

    Runs on CHECK_MODEL against a bounded prefix of the text, never the
    frontier model, so a mistaken upload costs a fraction of a cent
    instead of a full roast.
    """
    try:
        response = client.responses.create(
            model=CHECK_MODEL,
            instructions=CHECK_PROMPT,
            input=text[:CHECK_TEXT_PREFIX_CHARS],
        )
    except OpenAIError as exc:
        raise RoastError(
            "The resume check failed. Please try again in a moment."
        ) from exc

    output = (response.output_text or "").strip().upper()
    return output.startswith("YES")


def roast_resume(client: OpenAI, resume_text: str, target_role: str) -> str:
    """Frontier-tier core action: the roast itself.

    Returns a Markdown string beginning with ``SCORE: n/10`` on its own
    line, per prompts.ROAST_SYSTEM_PROMPT's output contract. No
    conversation history is sent -- every call is independent.
    """
    user_input = f"TARGET ROLE: {target_role}\n\nRESUME:\n{resume_text}"

    create_kwargs = dict(
        model=ROAST_MODEL,
        instructions=ROAST_SYSTEM_PROMPT,
        input=user_input,
        max_output_tokens=MAX_OUTPUT_TOKENS,
    )
    if ROAST_REASONING_EFFORT:
        # Non-reasoning models reject this parameter outright, so it's
        # only sent when config.py opts in.
        create_kwargs["reasoning"] = {"effort": ROAST_REASONING_EFFORT}

    try:
        response = client.responses.create(**create_kwargs)
    except OpenAIError as exc:
        raise RoastError(
            "The roast couldn't be generated. Please try again in a moment."
        ) from exc

    result = (response.output_text or "").strip()
    if not result:
        raise RoastError(
            "The model used its entire output budget without writing a "
            "critique. Try again, or raise MAX_OUTPUT_TOKENS in config.py."
        )

    return result


def parse_score(roast_text: str) -> str:
    """Extract and validate the score from the first line of a roast.

    Expects the output contract's ``SCORE: n/10`` line, with n an
    integer from 1 through 10. Raises RoastError rather than silently
    storing a malformed score.
    """
    first_line = roast_text.strip().splitlines()[0] if roast_text.strip() else ""
    match = _SCORE_LINE.match(first_line.strip())

    if not match:
        raise RoastError(
            "The model's response didn't start with the expected "
            "'SCORE: n/10' line, so it wasn't saved."
        )

    score = int(match.group(1))
    if not 1 <= score <= 10:
        raise RoastError(f"The model returned an out-of-range score: {score}.")

    return str(score)
