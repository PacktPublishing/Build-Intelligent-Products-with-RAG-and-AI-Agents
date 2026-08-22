"""Offline unit tests for the capped agent loop."""

import json
import unittest
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from prompts import (
    AGENT_SYSTEM_PROMPT,
    BROKEN_LINK_MESSAGE,
    COMPANY_SEARCH_ERROR_MESSAGE,
    INCOMPLETE_JOB_PAGE_MESSAGE,
    NON_JOB_PAGE_MESSAGE,
)
from roast import AGENT_LIMIT_MESSAGE, _run_tool, run_agentic_roast
from run_agent_smoke_tests import evaluate


def call(name: str, arguments: dict, call_id: str = "call_1"):
    return SimpleNamespace(
        type="function_call",
        name=name,
        arguments=json.dumps(arguments),
        call_id=call_id,
    )


def response(output, output_text=""):
    return SimpleNamespace(output=output, output_text=output_text)


class FakeResponses:
    def __init__(self, sequence):
        self.sequence = list(sequence)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.sequence.pop(0)


class FakeClient:
    def __init__(self, sequence):
        self.responses = FakeResponses(sequence)


class AgentLoopTests(unittest.TestCase):
    def test_tool_failures_override_scored_output_contract(self):
        self.assertIn(
            "these override the OUTPUT CONTRACT when triggered",
            AGENT_SYSTEM_PROMPT,
        )
        self.assertIn(BROKEN_LINK_MESSAGE, AGENT_SYSTEM_PROMPT)
        self.assertIn(COMPANY_SEARCH_ERROR_MESSAGE, AGENT_SYSTEM_PROMPT)
        self.assertIn(INCOMPLETE_JOB_PAGE_MESSAGE, AGENT_SYSTEM_PROMPT)
        self.assertIn(NON_JOB_PAGE_MESSAGE, AGENT_SYSTEM_PROMPT)
        self.assertIn("Do not produce a score, headings", AGENT_SYSTEM_PROMPT)

    def test_broken_premise_evaluation_requires_exact_safe_exit(self):
        trace = [{"type": "tool_call", "tool": "fetch_webpage"}]
        self.assertEqual(
            evaluate(
                "broken-premise",
                "fetch_webpage",
                trace,
                BROKEN_LINK_MESSAGE,
            ),
            [],
        )

        failures = evaluate(
            "broken-premise",
            "fetch_webpage",
            trace,
            "SCORE: 3/10\nPlease share a working link.",
        )
        self.assertTrue(failures)
        self.assertIn("exact safe exit phrase", failures[0])

    def test_distraction_evaluation_requires_exact_non_job_exit(self):
        trace = [{"type": "tool_call", "tool": "fetch_webpage"}]
        self.assertEqual(
            evaluate(
                "distraction",
                "fetch_webpage",
                trace,
                NON_JOB_PAGE_MESSAGE,
            ),
            [],
        )
        self.assertTrue(
            evaluate(
                "distraction",
                "fetch_webpage",
                trace,
                "SCORE: 2/10\nThis is a recipe.",
            )
        )

    def test_tool_then_final_response(self):
        client = FakeClient(
            [
                response([call("fetch_webpage", {"url": "https://example.com/job"})]),
                response([], "SCORE: 7/10\n\n## First impression\nSpecific."),
            ]
        )
        trace = []
        result = run_agentic_roast(
            client,
            "resume",
            "https://example.com/job",
            tool_handlers={"fetch_webpage": lambda url: "JOB POSTING: Python"},
            trace=trace,
        )

        self.assertTrue(result.startswith("SCORE: 7/10"))
        self.assertEqual([event["type"] for event in trace], ["tool_call", "final"])
        second_input = client.responses.calls[1]["input"]
        self.assertEqual(second_input[-1]["type"], "function_call_output")
        self.assertEqual(second_input[-1]["call_id"], "call_1")
        self.assertFalse(client.responses.calls[0]["parallel_tool_calls"])

    def test_hard_cap_stops_repeated_calls(self):
        client = FakeClient(
            [response([call("fetch_webpage", {"url": "https://example.com"}, f"c{i}")]) for i in range(3)]
        )
        result = run_agentic_roast(
            client,
            "resume",
            "https://example.com",
            tool_handlers={"fetch_webpage": lambda url: "same page"},
        )
        self.assertEqual(result, AGENT_LIMIT_MESSAGE)
        self.assertEqual(len(client.responses.calls), 3)

    def test_bad_json_becomes_observation(self):
        args, observation = _run_tool("fetch_webpage", "{bad", {})
        self.assertEqual(args, {})
        self.assertTrue(observation.startswith("Tool Error:"))

    def test_unknown_tool_becomes_observation(self):
        args, observation = _run_tool("send_email", "{}", {})
        self.assertEqual(args, {})
        self.assertIn("does not exist", observation)


if __name__ == "__main__":
    unittest.main()
