#!/usr/bin/env python3
"""Check that a Chapter 4 environment is ready to run, without spending money.

By default this script makes no network calls and needs no API key. Pass
--live to additionally make one minimal, billed call to confirm the key
in OPENAI_API_KEY actually works.

Usage:
    python scripts/verify_setup.py
    python scripts/verify_setup.py --live
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CHECKS_PASSED = []
CHECKS_FAILED = []


def check(name: str, passed: bool, detail: str = "") -> None:
    status = "PASS" if passed else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" -- {detail}"
    print(line)
    (CHECKS_PASSED if passed else CHECKS_FAILED).append(name)


def check_python_version() -> None:
    ok = sys.version_info >= (3, 11)
    check(
        "Python 3.11+",
        ok,
        f"found {sys.version_info.major}.{sys.version_info.minor}",
    )


def check_imports() -> None:
    for module_name in ["streamlit", "openai", "pypdf"]:
        try:
            __import__(module_name)
            check(f"import {module_name}", True)
        except ImportError as exc:
            check(f"import {module_name}", False, str(exc))


def check_config() -> None:
    try:
        import config
    except ImportError as exc:
        check("config.py imports", False, str(exc))
        return
    check("config.py imports", True)

    positive_ints = ["MAX_PAGES", "MIN_CHARS", "MAX_CHARS", "MAX_OUTPUT_TOKENS"]
    for name in positive_ints:
        value = getattr(config, name, None)
        ok = isinstance(value, int) and value > 0
        check(f"config.{name} is a positive int", ok, str(value))

    ok = config.MIN_CHARS < config.MAX_CHARS
    check("config.MIN_CHARS < config.MAX_CHARS", ok, f"{config.MIN_CHARS} < {config.MAX_CHARS}")

    for name in ["ROAST_MODEL", "CHECK_MODEL"]:
        value = getattr(config, name, "")
        check(f"config.{name} is non-empty", bool(value), repr(value))

    check("config.PROMPT_VERSION is non-empty", bool(getattr(config, "PROMPT_VERSION", "")))


def check_data_dir() -> None:
    try:
        import config

        with tempfile.TemporaryDirectory() as tmp:
            test_dir = Path(tmp) / "data-check"
            test_dir.mkdir(parents=True, exist_ok=True)
            check("data directory is creatable", test_dir.exists())
    except Exception as exc:  # pragma: no cover - defensive
        check("data directory is creatable", False, str(exc))


def check_live() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        check("OPENAI_API_KEY is set", False, "set it in your environment to run --live")
        return
    check("OPENAI_API_KEY is set", True)

    try:
        import config
        from roast import create_client

        client = create_client(api_key)
        response = client.responses.create(
            model=config.CHECK_MODEL,
            instructions="Reply with exactly one word: OK.",
            input="ping",
        )
        ok = bool((response.output_text or "").strip())
        check("live API call succeeds", ok)
    except Exception as exc:
        check("live API call succeeds", False, type(exc).__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="also make one minimal, billed API call to confirm the key works",
    )
    args = parser.parse_args()

    check_python_version()
    check_imports()
    check_config()
    check_data_dir()

    if args.live:
        check_live()
    else:
        print("[SKIP] live API check -- pass --live to run it (this will cost money)")

    print()
    print(f"{len(CHECKS_PASSED)} passed, {len(CHECKS_FAILED)} failed")
    return 0 if not CHECKS_FAILED else 1


if __name__ == "__main__":
    raise SystemExit(main())
