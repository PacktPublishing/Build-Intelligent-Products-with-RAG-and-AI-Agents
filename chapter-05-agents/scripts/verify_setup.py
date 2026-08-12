#!/usr/bin/env python3
"""Check that a Chapter 5 environment is ready to run, without spending money.

By default this script makes no network calls. It verifies that the local
Streamlit secret exists and is not the example placeholder, but never prints
its value. Pass --live to additionally make one minimal, billed call using
the key in the OPENAI_API_KEY environment variable.

Usage:
    python scripts/verify_setup.py
    python scripts/verify_setup.py --live
"""

import argparse
import os
import sys
import tempfile
import tomllib
from pathlib import Path

CHAPTER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CHAPTER_ROOT))

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
    for module_name in ["streamlit", "openai", "pypdf", "requests", "bs4"]:
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

    positive_ints = [
        "MAX_PAGES",
        "MIN_CHARS",
        "MAX_CHARS",
        "MAX_OUTPUT_TOKENS",
        "MAX_AGENT_STEPS",
        "MAX_INTENT_CHARS",
        "TOOL_TIMEOUT_SECONDS",
        "MAX_TOOL_REDIRECTS",
    ]
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


def check_agent_contract() -> None:
    try:
        from tool_schemas import AGENT_TOOLS
        from tools import TOOL_HANDLERS
    except ImportError as exc:
        check("agent modules import", False, str(exc))
        return

    check("agent modules import", True)
    schema_names = {schema.get("name") for schema in AGENT_TOOLS}
    handler_names = set(TOOL_HANDLERS)
    check(
        "tool schemas match Python handlers",
        schema_names == handler_names,
        f"schemas={sorted(schema_names)}, handlers={sorted(handler_names)}",
    )
    check("exactly two read-only tools", len(AGENT_TOOLS) == 2, str(len(AGENT_TOOLS)))
    check(
        "all tool schemas use strict mode",
        all(schema.get("strict") is True for schema in AGENT_TOOLS),
    )


def check_data_dir() -> None:
    try:
        import config

        with tempfile.TemporaryDirectory() as tmp:
            test_dir = Path(tmp) / "data-check"
            test_dir.mkdir(parents=True, exist_ok=True)
            check("data directory is creatable", test_dir.exists())
    except Exception as exc:  # pragma: no cover - defensive
        check("data directory is creatable", False, str(exc))


def check_local_secret() -> None:
    """Validate local key configuration without displaying the key."""
    secret_path = CHAPTER_ROOT / ".streamlit" / "secrets.toml"
    if not secret_path.exists():
        check(
            "local Streamlit secret exists",
            False,
            "copy .streamlit/secrets.example.toml to .streamlit/secrets.toml",
        )
        return

    check("local Streamlit secret exists", True)
    try:
        with open(secret_path, "rb") as file:
            value = tomllib.load(file).get("OPENAI_API_KEY", "")
    except (OSError, tomllib.TOMLDecodeError) as exc:
        check("local Streamlit secret is valid TOML", False, type(exc).__name__)
        return

    check("local Streamlit secret is valid TOML", True)
    configured = (
        isinstance(value, str)
        and len(value.strip()) >= 20
        and value.strip() not in {"replace-with-your-key", "your_api_key_here"}
    )
    check(
        "OPENAI_API_KEY is configured for Streamlit",
        configured,
        "the value is intentionally never printed",
    )

    root_ignore = CHAPTER_ROOT.parent / ".gitignore"
    ignored = root_ignore.exists() and "**/.streamlit/secrets.toml" in root_ignore.read_text(
        encoding="utf-8"
    ).splitlines()
    check("Streamlit secret is covered by .gitignore", ignored)


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
    check_agent_contract()
    check_data_dir()
    check_local_secret()

    if args.live:
        check_live()
    else:
        print("[SKIP] live API check -- pass --live to run it (this will cost money)")

    print()
    print(f"{len(CHECKS_PASSED)} passed, {len(CHECKS_FAILED)} failed")
    return 0 if not CHECKS_FAILED else 1


if __name__ == "__main__":
    raise SystemExit(main())
