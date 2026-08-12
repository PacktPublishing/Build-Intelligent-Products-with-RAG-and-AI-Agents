#!/usr/bin/env python3
"""Run the core action from a terminal, with no UI anywhere near it.

This is the "engine on a stand" from the chapter's build order: it lets
you test is_resume and roast_resume against a real PDF before app.py
exists, or afterwards, whenever you're iterating on the prompt.

WARNING: this script makes real, billed calls to your model provider
(both the budget check and, unless validation fails, the frontier
roast).

Usage:
    python scripts/run_core_action.py --pdf smoke-tests/duty-lister-resume.pdf \\
        --role "Senior Data Analyst"

The API key is read from the OPENAI_API_KEY environment variable, not
from Streamlit secrets, so this script runs with no Streamlit
dependency at all.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import IngestError, extract_resume_text  # noqa: E402
from roast import RoastError, create_client, is_resume, parse_score, roast_resume  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, help="Path to a resume PDF")
    parser.add_argument("--role", required=True, help="Target role to roast against")
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
            print("The budget-tier check says this doesn't look like a resume. Stopping "
                  "before the frontier call.", file=sys.stderr)
            return 1

        result = roast_resume(client, text, args.role)
    except RoastError as exc:
        print(f"Roast failed: {exc}", file=sys.stderr)
        return 1

    try:
        score = parse_score(result)
    except RoastError as exc:
        print(f"Warning: {exc}", file=sys.stderr)
        score = "unknown"

    print(f"\nSCORE: {score}/10\n")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
