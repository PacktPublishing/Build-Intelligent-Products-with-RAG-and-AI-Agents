#!/usr/bin/env python3
"""Run the four Chapter 5 trajectory tests.

The model call is real under ``--live``, but tool outputs are deterministic
fixtures. That isolates routing and stopping behaviour from job-board
uptime, anti-bot pages, and changing search rankings.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CHAPTER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CHAPTER_ROOT))

from prompts import BROKEN_LINK_MESSAGE, NON_JOB_PAGE_MESSAGE  # noqa: E402

PDF_PATH = CHAPTER_ROOT / "smoke-tests" / "duty-lister-resume.pdf"
RESULTS_DIR = CHAPTER_ROOT / "smoke-tests" / "results"


def fake_fetch(url: str) -> str:
    if "missing" in url:
        return "Tool Error: Could not fetch the webpage. Details: 404 Not Found"
    if "recipe" in url:
        return "Chocolate chip cookie recipe: flour, butter, sugar, eggs; bake at 180 C."
    return (
        "JOB POSTING: Data Engineer. Build reliable Python data pipelines; "
        "strong SQL, distributed systems, ownership, and measurable impact required."
    )


def fake_search(company_name: str) -> str:
    return (
        f"Public search results for {company_name}: engineering teams value "
        "ownership, collaboration, reliable systems, and measurable customer impact."
    )


CASES = {
    "direct-hit": {
        "intent": (
            "Critique my resume against this role: "
            "https://jobs.example.com/data-engineer"
        ),
        "tool": "fetch_webpage",
    },
    "ambiguous-intent": {
        "intent": "I want to work as a backend developer at Airbnb. Is my resume good enough?",
        "tool": "search_company_culture",
    },
    "broken-premise": {
        "intent": "Critique it for https://jobs.example.com/missing",
        "tool": "fetch_webpage",
    },
    "distraction": {
        "intent": "Critique it for https://recipes.example.com/cookies",
        "tool": "fetch_webpage",
    },
}


def evaluate(case_name: str, expected_tool: str, trace: list[dict], output: str) -> list[str]:
    failures = []
    calls = [event for event in trace if event["type"] == "tool_call"]
    names = [event["tool"] for event in calls]
    if names != [expected_tool]:
        failures.append(f"expected exactly [{expected_tool}], got {names}")
    if case_name == "broken-premise" and output.strip() != BROKEN_LINK_MESSAGE:
        failures.append(
            "broken URL did not return the exact safe exit phrase; "
            f"expected {BROKEN_LINK_MESSAGE!r}, got {output.strip()!r}"
        )
    if case_name == "distraction" and output.strip() != NON_JOB_PAGE_MESSAGE:
        failures.append("recipe guardrail did not return the exact safe exit phrase")
    return failures


def run_case(client, resume_text: str, name: str, definition: dict) -> dict:
    from roast import run_agentic_roast

    trace = []
    output = run_agentic_roast(
        client,
        resume_text,
        definition["intent"],
        tool_handlers={
            "fetch_webpage": fake_fetch,
            "search_company_culture": fake_search,
        },
        trace=trace,
    )
    failures = evaluate(name, definition["tool"], trace, output)
    return {
        "case": name,
        "intent": definition["intent"],
        "expected_tool": definition["tool"],
        "trace": trace,
        "output": output,
        "passed_automatic_checks": not failures,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="make real, billed API calls")
    parser.add_argument("--case", choices=CASES, help="run one case")
    args = parser.parse_args()

    selected = {args.case: CASES[args.case]} if args.case else CASES
    if not args.live:
        print("Dry run -- no API calls will be made.\n")
        for name, case in selected.items():
            print(f"- {name}: expect {case['tool']} for {case['intent']}")
        return 0

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Set OPENAI_API_KEY before using --live.", file=sys.stderr)
        return 1

    from ingest import extract_resume_text
    from roast import create_client

    with open(PDF_PATH, "rb") as f:
        resume_text = extract_resume_text(f)
    client = create_client(api_key)

    results = []
    failed = False
    for name, case in selected.items():
        print(f"\n=== {name} ===")
        record = run_case(client, resume_text, name, case)
        results.append(record)
        print("PASS" if record["passed_automatic_checks"] else "FAIL")
        for failure in record["failures"]:
            print(f"- {failure}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS_DIR / f"agent-trajectories-{stamp}.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved full trajectories and outputs to {path}")

    failed = any(not item["passed_automatic_checks"] for item in results)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
