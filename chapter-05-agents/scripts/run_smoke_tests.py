#!/usr/bin/env python3
"""Run the five Chapter 4 resume-quality fixtures through the v2 agent.

These regression tests use generic role intents, so the agent should
bypass both tools and preserve the grounded roast quality from Chapter 4.
The default is a free dry run; ``--live`` makes billed API calls.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CHAPTER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CHAPTER_ROOT))

SMOKE_TESTS_DIR = CHAPTER_ROOT / "smoke-tests"
RESULTS_DIR = SMOKE_TESTS_DIR / "results"

FIXTURES = {
    "strong-senior-resume.pdf": "Senior Software Engineer",
    "duty-lister-resume.pdf": "Marketing Manager",
    "career-changer-resume.pdf": "Data Analyst",
    "sparse-graduate-resume.pdf": "Software Engineer",
    "mismatched-role-resume.pdf": "Fintech Chief Technology Officer",
}

REVIEW_CHECKLIST = [
    "Did the generic-role intent bypass both tools?",
    "Did every criticism quote or directly reference the resume?",
    "Did the structure hold (SCORE, six headings, three actions)?",
    "Did the tone remain direct but not cruel?",
    "Did the model avoid inventing facts?",
    "Did it preserve the Chapter 4 quality baseline?",
]


def run_one(fixture_name: str, intent: str, live: bool) -> dict:
    pdf_path = SMOKE_TESTS_DIR / fixture_name
    record = {
        "fixture": fixture_name,
        "intent": intent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "live": live,
    }
    if not pdf_path.exists():
        record["error"] = f"missing fixture: {pdf_path}"
        return record
    if not live:
        record["status"] = "dry-run (no API call made)"
        return record

    import config
    from ingest import IngestError, extract_resume_text
    from roast import RoastError, create_client, parse_score, run_agentic_roast

    record.update(
        roast_model=config.ROAST_MODEL,
        prompt_version=config.PROMPT_VERSION,
    )
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        record["error"] = "OPENAI_API_KEY is not set"
        return record

    try:
        with open(pdf_path, "rb") as f:
            text = extract_resume_text(f)
        trace = []
        result = run_agentic_roast(create_client(api_key), text, intent, trace=trace)
        record["trace"] = trace
        record["output"] = result
        record["score"] = parse_score(result) if result.startswith("SCORE:") else None
    except (IngestError, RoastError) as exc:
        record["error"] = str(exc)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="make real, billed API calls")
    parser.add_argument("--fixture", choices=FIXTURES, help="run one fixture")
    args = parser.parse_args()

    selected = (
        {args.fixture: FIXTURES[args.fixture]} if args.fixture else FIXTURES
    )
    if not args.live:
        print("Dry run -- no API calls will be made. Pass --live to run for real.\n")

    results = []
    for fixture, intent in selected.items():
        print(f"- {fixture} -> intent: {intent}")
        record = run_one(fixture, intent, args.live)
        results.append(record)
        if record.get("error"):
            print(f"  ERROR: {record['error']}")

    if args.live:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = RESULTS_DIR / f"regression-{stamp}.json"
        path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nSaved results to {path}")

    print("\nHuman review checklist:")
    for item in REVIEW_CHECKLIST:
        print(f"  [ ] {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
