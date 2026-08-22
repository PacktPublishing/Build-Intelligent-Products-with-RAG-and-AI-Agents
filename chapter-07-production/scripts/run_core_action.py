#!/usr/bin/env python3
"""Run the Chapter 5 agent core from a terminal, with no UI attached.

WARNING: this script makes real, billed model calls and may make
read-only web requests when the model chooses a tool.

Usage:
    python scripts/run_core_action.py \
        --pdf smoke-tests/duty-lister-resume.pdf \
        --intent "I want a data role at Airbnb"
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import IngestError, extract_resume_text  # noqa: E402
from roast import (  # noqa: E402
    RoastError,
    create_client,
    is_resume,
    parse_score,
    run_agentic_roast,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, help="Path to a resume PDF")
    parser.add_argument(
        "--intent",
        required=True,
        help="Job URL, company, role, or other application intent",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Set the OPENAI_API_KEY environment variable and try again.", file=sys.stderr)
        return 1

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"No such file: {pdf_path}", file=sys.stderr)
        return 1

    print("This will make real, billed API calls. Continuing...", file=sys.stderr)
    client = create_client(api_key)

    try:
        with open(pdf_path, "rb") as f:
            text = extract_resume_text(f)
    except IngestError as exc:
        print(f"Ingestion failed: {exc}", file=sys.stderr)
        return 1

    try:
        if not is_resume(client, text):
            print(
                "The budget-tier check says this isn't a resume. Stopping "
                "before the agent call.",
                file=sys.stderr,
            )
            return 1
        result = run_agentic_roast(client, text, args.intent)
    except RoastError as exc:
        print(f"Roast failed: {exc}", file=sys.stderr)
        return 1

    if result.startswith("SCORE:"):
        try:
            print(f"\nParsed score: {parse_score(result)}/10\n")
        except RoastError as exc:
            print(f"Warning: {exc}", file=sys.stderr)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
