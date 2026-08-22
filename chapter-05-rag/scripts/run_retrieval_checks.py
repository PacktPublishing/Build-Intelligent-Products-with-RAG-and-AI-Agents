#!/usr/bin/env python3
"""Evaluate retrieval separately from generated feedback.

Without --live this prints the role-to-expected-rubric contract and makes
no API calls. With --live it embeds each role and reports the returned IDs.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

CASES = {
    "Senior Data Analyst": "DA-01",
    "Marketing Manager": "MKT-01",
    "Senior Software Engineer": "SWE-01",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="make billed embedding calls")
    args = parser.parse_args()
    print("Retrieval evaluation contract:")
    for role, expected in CASES.items():
        print(f"- {role}: top result should include {expected}")
    if not args.live:
        print("\nDry run: no API calls. Pass --live to execute retrieval.")
        return 0
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is required for --live.", file=sys.stderr)
        return 1
    from config import CORPUS_PATH
    from corpus import load_rubrics
    from retrieval import build_index, retrieve_rubrics
    from roast import create_client

    client = create_client(api_key)
    corpus = load_rubrics(ROOT / CORPUS_PATH)
    index = build_index(client, corpus)
    failures = 0
    for role, expected in CASES.items():
        results = retrieve_rubrics(client, role, index)
        ids = [result.chunk.chunk_id for result in results]
        passed = expected in ids
        failures += not passed
        print(f"[{'PASS' if passed else 'FAIL'}] {role}: {', '.join(ids)}")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
