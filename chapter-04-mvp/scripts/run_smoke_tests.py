#!/usr/bin/env python3
"""Run the five smoke-test resumes and save outputs for manual review.

A prompt isn't done when it works on your own resume -- it's done when
it survives inputs chosen to break it. This script runs is_resume and
roast_resume against the five synthetic resumes in smoke-tests/, each
targeting a specific failure mode (see smoke-tests/README.md).

By default (no --live) this script makes NO API calls -- it only prints
what it would run, so you can check the fixture list and role mapping
for free. Pass --live to make real, billed calls.

Usage:
    python scripts/run_smoke_tests.py                 # dry run, no cost
    python scripts/run_smoke_tests.py --live           # real calls, real cost
    python scripts/run_smoke_tests.py --live --fixture duty-lister-resume.pdf
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

# Fixture -> target role. Each pairing targets one failure mode from
# smoke-tests/README.md.
FIXTURES = {
    "strong-senior-resume.pdf": "Senior Software Engineer",
    "duty-lister-resume.pdf": "Marketing Manager",
    "career-changer-resume.pdf": "Data Analyst",
    "sparse-graduate-resume.pdf": "Software Engineer",
    "mismatched-role-resume.pdf": "Fintech Chief Technology Officer",
}

REVIEW_CHECKLIST = [
    "Did every criticism quote or directly reference the resume?",
    "Did the structure hold (SCORE line, all six headings, three numbered actions)?",
    "Did the tone remain direct but not cruel?",
    "Did the model avoid inventing facts?",
    "Did it acknowledge genuine strengths?",
    "Did it engage honestly with the target-role mismatch?",
    "Would the intended user find this worth the wait?",
]


def run_one(fixture_name: str, role: str, live: bool) -> dict:
    pdf_path = SMOKE_TESTS_DIR / fixture_name
    record = {
        "fixture": fixture_name,
        "role": role,
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
    from roast import RoastError, create_client, is_resume, parse_score, roast_resume

    record["roast_model"] = config.ROAST_MODEL
    record["check_model"] = config.CHECK_MODEL
    record["prompt_version"] = config.PROMPT_VERSION

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        record["error"] = "OPENAI_API_KEY is not set"
        return record

    client = create_client(api_key)

    try:
        with open(pdf_path, "rb") as f:
            text = extract_resume_text(f)
    except IngestError as exc:
        record["error"] = f"ingestion failed: {exc}"
        return record

    try:
        if not is_resume(client, text):
            record["error"] = "budget-tier check rejected this fixture as a non-resume"
            return record
        result = roast_resume(client, text, role)
    except RoastError as exc:
        record["error"] = f"roast failed: {exc}"
        return record

    try:
        record["score"] = parse_score(result)
    except RoastError as exc:
        record["score"] = None
        record["score_error"] = str(exc)

    record["output"] = result
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="make real, billed API calls (default: dry run, no cost)",
    )
    parser.add_argument(
        "--fixture",
        help="run a single fixture file name instead of all five",
    )
    args = parser.parse_args()

    fixtures = FIXTURES
    if args.fixture:
        if args.fixture not in FIXTURES:
            print(f"Unknown fixture: {args.fixture}", file=sys.stderr)
            print(f"Known fixtures: {', '.join(FIXTURES)}", file=sys.stderr)
            return 1
        fixtures = {args.fixture: FIXTURES[args.fixture]}

    if not args.live:
        print("Dry run -- no API calls will be made. Pass --live to run for real.\n")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = []

    for fixture_name, role in fixtures.items():
        print(f"- {fixture_name}  ->  target role: {role}")
        record = run_one(fixture_name, role, args.live)
        results.append(record)
        if record.get("error"):
            print(f"  ERROR: {record['error']}")
        elif args.live:
            print(f"  score: {record.get('score')}")

    if args.live:
        out_path = RESULTS_DIR / f"smoke-{run_stamp}.json"
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nSaved results to {out_path} (this directory is gitignored).")

    print("\nHuman review checklist -- read each saved output against these:")
    for item in REVIEW_CHECKLIST:
        print(f"  [ ] {item}")
    print(
        "\nThis checklist cannot be fully automated -- prompt quality is a "
        "judgment call, and this script only gets you the outputs to judge."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
