"""ResumeRoast's capped multi-step agent engine.

The module remains independent of Streamlit and does not create a paid
client on import, preserving Chapter 4's testable core-action boundary.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from typing import Any

from openai import OpenAI, OpenAIError

from config import (
    CHECK_MODEL,
    MAX_AGENT_STEPS,
    MAX_OUTPUT_TOKENS,
    ROAST_MODEL,
    ROAST_REASONING_EFFORT,
)
from prompts import AGENT_SYSTEM_PROMPT
from tool_schemas import AGENT_TOOLS
from tools import TOOL_HANDLERS

CHECK_PROMPT = (
    "You check whether a document is a resume or CV. "
    "Reply with exactly one word: YES or NO."
)
CHECK_TEXT_PREFIX_CHARS = 3000
AGENT_LIMIT_MESSAGE = (
    "Agent Error: I had to stop thinking because the task became too complex. "
    "Please try providing a more direct prompt."
)

_SCORE_LINE = re.compile(r"^SCORE:\s*(\d{1,2})\s*/\s*10\s*$")


class RoastError(Exception):
    """Raised with a user-facing message when the model API cannot be used."""


def create_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def is_resume(client: OpenAI, text: str) -> bool:
    """Use the budget tier to reject non-resumes before the agent call."""
    try:
        response = client.responses.create(
            model=CHECK_MODEL,
            instructions=CHECK_PROMPT,
            input=text[:CHECK_TEXT_PREFIX_CHARS],
        )
    except OpenAIError as exc:
        raise RoastError("The resume check failed. Please try again in a moment.") from exc

    return (response.output_text or "").strip().upper().startswith("YES")


def _record_event(trace: list[dict[str, Any]] | None, event: dict[str, Any]) -> None:
    if trace is not None:
        trace.append(event)


def _run_tool(
    tool_name: str,
    raw_arguments: str,
    handlers: Mapping[str, Callable[..., str]],
) -> tuple[dict[str, Any], str]:
    """Parse one model request and turn all failures into observations."""
    try:
        arguments = json.loads(raw_arguments)
        if not isinstance(arguments, dict):
            raise ValueError("tool arguments must be a JSON object")

        handler = handlers.get(tool_name)
        if handler is None:
            return arguments, f"Tool Error: Tool {tool_name!r} does not exist."

        observation = handler(**arguments)
        return arguments, str(observation)
    except Exception as exc:
        return {}, f"Tool Error: Could not execute {tool_name}. Details: {exc}"


def run_agentic_roast(
    client: OpenAI,
    resume_text: str,
    user_intent: str,
    *,
    max_steps: int = MAX_AGENT_STEPS,
    tool_handlers: Mapping[str, Callable[..., str]] | None = None,
    trace: list[dict[str, Any]] | None = None,
) -> str:
    """Run a bounded ReAct loop and return the final Markdown response.

    ``trace`` is an optional list populated with model/tool events for the
    Chapter 5 trajectory tests. The same action events are printed to the
    terminal so a reader can audit a live Streamlit run.
    """
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")

    handlers = tool_handlers or TOOL_HANDLERS
    input_items: list[Any] = [
        {
            "role": "user",
            "content": f"RESUME:\n{resume_text}\n\nUSER INTENT:\n{user_intent}",
        }
    ]

    for step in range(1, max_steps + 1):
        create_kwargs: dict[str, Any] = {
            "model": ROAST_MODEL,
            "instructions": AGENT_SYSTEM_PROMPT,
            "input": input_items,
            "tools": AGENT_TOOLS,
            "tool_choice": "auto",
            "parallel_tool_calls": False,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
        }
        if ROAST_REASONING_EFFORT:
            create_kwargs["reasoning"] = {"effort": ROAST_REASONING_EFFORT}

        try:
            response = client.responses.create(**create_kwargs)
        except OpenAIError as exc:
            raise RoastError(
                "The agent couldn't generate a roast. Please try again in a moment."
            ) from exc

        # Responses API history includes the model's complete output items,
        # including reasoning and function calls, before tool observations.
        input_items.extend(response.output)
        tool_calls = [item for item in response.output if item.type == "function_call"]

        if not tool_calls:
            result = (response.output_text or "").strip()
            if not result:
                raise RoastError(
                    "The model used its output budget without writing a critique. "
                    "Try again, or raise MAX_OUTPUT_TOKENS in config.py."
                )
            _record_event(trace, {"step": step, "type": "final"})
            print(f"[agent step {step}/{max_steps}] final response")
            return result

        for tool_call in tool_calls:
            arguments, observation = _run_tool(
                tool_call.name,
                tool_call.arguments,
                handlers,
            )
            event = {
                "step": step,
                "type": "tool_call",
                "tool": tool_call.name,
                "arguments": arguments,
                "observation": observation,
            }
            _record_event(trace, event)

            preview = " ".join(observation.split())[:160]
            print(
                f"[agent step {step}/{max_steps}] action={tool_call.name} "
                f"arguments={arguments!r}"
            )
            print(f"[agent step {step}/{max_steps}] observation={preview}")

            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": observation,
                }
            )

    _record_event(trace, {"step": max_steps, "type": "limit_reached"})
    print(f"[agent] stopped after hard cap of {max_steps} model steps")
    return AGENT_LIMIT_MESSAGE


def parse_score(roast_text: str) -> str:
    """Extract an integer 1-10 score from the response contract."""
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
