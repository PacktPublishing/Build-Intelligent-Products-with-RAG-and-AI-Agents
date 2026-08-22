#!/usr/bin/env python3
"""Run grounded answer checks after retrieval passes.

The default dry run costs nothing. With --live, each synthetic resume is
retrieved and roasted, then the script saves the source IDs and response for
human review. It does not pretend that prose quality is fully automatable.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIXTURES = {
    "duty-lister-resume.pdf": {"role": "Marketing Manager", "expected": "MKT-01"},
    "career-changer-resume.pdf": {"role": "Senior Data Analyst", "expected": "DA-01"},
    "strong-senior-resume.pdf": {"role": "Senior Software Engineer", "expected": "SWE-01"},
}
SMOKE_DIR = ROOT / "smoke-tests"
RESULTS_DIR = SMOKE_DIR / "results"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="make billed embedding and generation calls")
    args = parser.parse_args()
    print("Grounded answer review contract:")
    for name, case in FIXTURES.items():
        print(f"- {name}: role {case['role']}; expected evidence includes {case['expected']}")
    if not args.live:
        print("\nDry run: no API calls. Pass --live to save responses for review.")
        return 0

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is required for --live.", file=sys.stderr)
        return 1

    from config import CORPUS_PATH
    from corpus import load_rubrics
    from ingest import extract_resume_text
    from retrieval import build_index
    from roast import create_client, is_resume, roast_resume

    client = create_client(api_key)
    index = build_index(client, load_rubrics(ROOT / CORPUS_PATH))
    records = []
    failures = 0
    for name, case in FIXTURES.items():
        pdf_path = SMOKE_DIR / name
        with pdf_path.open("rb") as file:
            resume = extract_resume_text(file)
        if not is_resume(client, resume):
            print(f"[FAIL] {name}: resume check rejected fixture")
            failures += 1
            continue
        result = roast_resume(client, resume, case["role"], index)
        evidence_ids = [match.chunk.chunk_id for match in result.evidence]
        passed = case["expected"] in evidence_ids
        failures += not passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name}: {', '.join(evidence_ids)}")
        records.append({"fixture": name, "role": case["role"], "evidence_ids": evidence_ids, "output": result.text})

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / f"grounded-smoke-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    output.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"\nSaved outputs to {output}")
    print("Review every saved output for resume-specific claims, relevant source IDs, and useful actions.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
