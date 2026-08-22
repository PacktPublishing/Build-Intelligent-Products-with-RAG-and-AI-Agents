"""Retrieve private evidence, then run a bounded agent loop."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from openai import OpenAI, OpenAIError

from config import CHECK_MODEL, MAX_AGENT_STEPS, MAX_OUTPUT_TOKENS, ROAST_MODEL, ROAST_REASONING_EFFORT
from prompts import AGENT_SYSTEM_PROMPT, CHECK_PROMPT
from retrieval import EmbeddedCorpus, RetrievedChunk, RetrievalError, format_evidence, retrieve_rubrics
from tool_schemas import AGENT_TOOLS
from tools import TOOL_HANDLERS

CHECK_TEXT_PREFIX_CHARS = 3_000
AGENT_LIMIT_MESSAGE = "Agent Error: I had to stop because the task became too complex. Please try a more direct prompt."
_SCORE_LINE = re.compile(r"^SCORE:\s*(\d{1,2})\s*/\s*10\s*$")


class RoastError(Exception):
    """Raised with a safe, user-facing message."""


@dataclass(frozen=True)
class AgentRoast:
    text: str
    evidence: list[RetrievedChunk]
    trace: list[dict[str, Any]]


def create_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def is_resume(client: OpenAI, text: str) -> bool:
    try:
        response = client.responses.create(model=CHECK_MODEL, instructions=CHECK_PROMPT, input=text[:CHECK_TEXT_PREFIX_CHARS])
    except OpenAIError as exc:
        raise RoastError("The resume check failed. Please try again shortly.") from exc
    return (response.output_text or "").strip().upper().startswith("YES")


def _run_tool(tool_name: str, raw_arguments: str, handlers: Mapping[str, Callable[..., str]]) -> tuple[dict[str, Any], str]:
    try:
        arguments = json.loads(raw_arguments)
        if not isinstance(arguments, dict):
            raise ValueError("tool arguments must be a JSON object")
        handler = handlers.get(tool_name)
        if handler is None:
            return arguments, f"Tool Error: Tool {tool_name!r} does not exist."
        return arguments, str(handler(**arguments))
    except Exception as exc:
        return {}, f"Tool Error: Could not execute {tool_name}. Details: {exc}"


def run_agentic_roast(client: OpenAI, resume_text: str, user_intent: str, *, evidence_text: str = "", max_steps: int = MAX_AGENT_STEPS, tool_handlers: Mapping[str, Callable[..., str]] | None = None, trace: list[dict[str, Any]] | None = None) -> str:
    """Run the testable loop after the caller has obtained curated evidence."""
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")
    trace = trace if trace is not None else []
    handlers = tool_handlers or TOOL_HANDLERS
    input_items: list[Any] = [{"role": "user", "content": f"USER INTENT:\n{user_intent}\n\nRETRIEVED RUBRIC EVIDENCE:\n{evidence_text}\n\nRESUME:\n{resume_text}"}]
    for step in range(1, max_steps + 1):
        kwargs: dict[str, Any] = {"model": ROAST_MODEL, "instructions": AGENT_SYSTEM_PROMPT, "input": input_items, "tools": AGENT_TOOLS, "tool_choice": "auto", "parallel_tool_calls": False, "max_output_tokens": MAX_OUTPUT_TOKENS}
        if ROAST_REASONING_EFFORT:
            kwargs["reasoning"] = {"effort": ROAST_REASONING_EFFORT}
        try:
            response = client.responses.create(**kwargs)
        except OpenAIError as exc:
            raise RoastError("The agent couldn't generate a roast. Please try again shortly.") from exc
        input_items.extend(response.output)
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            text = (response.output_text or "").strip()
            if not text:
                raise RoastError("The model returned no critique. Try again or increase MAX_OUTPUT_TOKENS.")
            trace.append({"step": step, "type": "final"})
            print(f"[agent step {step}/{max_steps}] final response")
            return text
        for call in calls:
            arguments, observation = _run_tool(call.name, call.arguments, handlers)
            trace.append({"step": step, "type": "tool_call", "tool": call.name, "arguments": arguments, "observation": observation})
            print(f"[agent step {step}/{max_steps}] action={call.name} arguments={arguments!r}")
            print(f"[agent step {step}/{max_steps}] observation={' '.join(observation.split())[:160]}")
            input_items.append({"type": "function_call_output", "call_id": call.call_id, "output": observation})
    trace.append({"step": max_steps, "type": "limit_reached"})
    print(f"[agent] stopped after hard cap of {max_steps} model steps")
    return AGENT_LIMIT_MESSAGE


def roast_resume(client: OpenAI, resume_text: str, user_intent: str, index: EmbeddedCorpus, *, tool_handlers: Mapping[str, Callable[..., str]] | None = None) -> AgentRoast:
    """Retrieve role evidence first, then let the agent use public tools if earned."""
    try:
        evidence = retrieve_rubrics(client, user_intent, index)
    except RetrievalError as exc:
        raise RoastError(str(exc)) from exc
    trace: list[dict[str, Any]] = []
    text = run_agentic_roast(client, resume_text, user_intent, evidence_text=format_evidence(evidence), tool_handlers=tool_handlers, trace=trace)
    return AgentRoast(text=text, evidence=evidence, trace=trace)


def parse_score(roast_text: str) -> str:
    first_line = roast_text.strip().splitlines()[0] if roast_text.strip() else ""
    match = _SCORE_LINE.match(first_line)
    if not match:
        raise RoastError("The response did not start with the expected SCORE: n/10 line.")
    score = int(match.group(1))
    if not 1 <= score <= 10:
        raise RoastError(f"The model returned an out-of-range score: {score}.")
    return str(score)
