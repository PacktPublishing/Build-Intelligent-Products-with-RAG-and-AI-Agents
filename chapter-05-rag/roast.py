"""Core RAG action: resume and role in, grounded roast and evidence out."""

import re
from dataclasses import dataclass

from openai import OpenAI, OpenAIError

from config import CHECK_MODEL, MAX_OUTPUT_TOKENS, ROAST_MODEL, ROAST_REASONING_EFFORT
from prompts import CHECK_PROMPT, ROAST_SYSTEM_PROMPT
from retrieval import EmbeddedCorpus, RetrievedChunk, RetrievalError, format_evidence, retrieve_rubrics

CHECK_TEXT_PREFIX_CHARS = 3_000
_SCORE_LINE = re.compile(r"^SCORE:\s*(\d{1,2})\s*/\s*10\s*$")


class RoastError(Exception):
    """Raised with a safe user-facing message for an unavailable model action."""


@dataclass(frozen=True)
class GroundedRoast:
    text: str
    evidence: list[RetrievedChunk]


def create_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def is_resume(client: OpenAI, text: str) -> bool:
    try:
        response = client.responses.create(
            model=CHECK_MODEL, instructions=CHECK_PROMPT, input=text[:CHECK_TEXT_PREFIX_CHARS]
        )
    except OpenAIError as exc:
        raise RoastError("The resume check failed. Please try again shortly.") from exc
    return (response.output_text or "").strip().upper().startswith("YES")


def roast_resume(
    client: OpenAI, resume_text: str, target_role: str, index: EmbeddedCorpus
) -> GroundedRoast:
    """Retrieve rubric evidence, then make one grounded generation call."""
    try:
        evidence = retrieve_rubrics(client, target_role, index)
        evidence_text = format_evidence(evidence)
    except RetrievalError as exc:
        raise RoastError(str(exc)) from exc

    user_input = (
        f"TARGET ROLE:\n{target_role}\n\n"
        f"RETRIEVED RUBRIC EVIDENCE:\n{evidence_text}\n\n"
        f"RESUME:\n{resume_text}"
    )
    kwargs = {
        "model": ROAST_MODEL,
        "instructions": ROAST_SYSTEM_PROMPT,
        "input": user_input,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
    if ROAST_REASONING_EFFORT:
        kwargs["reasoning"] = {"effort": ROAST_REASONING_EFFORT}
    try:
        response = client.responses.create(**kwargs)
    except OpenAIError as exc:
        raise RoastError("The grounded roast could not be generated. Please try again shortly.") from exc

    text = (response.output_text or "").strip()
    if not text:
        raise RoastError("The model returned no critique. Try again or increase MAX_OUTPUT_TOKENS.")
    return GroundedRoast(text=text, evidence=evidence)


def parse_score(roast_text: str) -> str:
    first_line = roast_text.strip().splitlines()[0] if roast_text.strip() else ""
    match = _SCORE_LINE.match(first_line)
    if not match:
        raise RoastError("The response did not start with the expected SCORE: n/10 line.")
    score = int(match.group(1))
    if not 1 <= score <= 10:
        raise RoastError(f"The model returned an out-of-range score: {score}.")
    return str(score)
