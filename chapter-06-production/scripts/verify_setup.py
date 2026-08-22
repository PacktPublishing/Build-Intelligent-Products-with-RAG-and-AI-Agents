#!/usr/bin/env python3
"""Verify that the Chapter 6 project is safe and ready to deploy.

The default checks are local and make no network calls. Pass --live to
make one minimal billed OpenAI request after all local checks pass.
No secret value is ever printed.
"""

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlparse


CHAPTER_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = CHAPTER_ROOT.parent
sys.path.insert(0, str(CHAPTER_ROOT))

CHECKS_PASSED: list[str] = []
CHECKS_FAILED: list[str] = []

REQUIRED_PACKAGES = {
    "streamlit": "1.60.0",
    "openai": "2.48.0",
    "pypdf": "6.14.2",
    "requests": "2.32.5",
    "beautifulsoup4": "4.14.3",
    "supabase": "2.31.0",
}


def check(name: str, passed: bool, detail: str = "") -> None:
    status = "PASS" if passed else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" -- {detail}"
    print(line)
    (CHECKS_PASSED if passed else CHECKS_FAILED).append(name)


def check_python_version() -> None:
    ok = sys.version_info >= (3, 11)
    found = f"{sys.version_info.major}.{sys.version_info.minor}"
    check("Python 3.11+", ok, f"found {found}")


def check_imports() -> None:
    for module_name in [
        "streamlit",
        "openai",
        "pypdf",
        "requests",
        "bs4",
        "supabase",
    ]:
        try:
            __import__(module_name)
            check(f"import {module_name}", True)
        except ImportError as exc:
            check(f"import {module_name}", False, str(exc))


def check_requirements() -> None:
    path = CHAPTER_ROOT / "requirements.txt"
    if not path.exists():
        check("requirements.txt exists", False)
        return

    check("requirements.txt exists", True)
    lines = {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    for package, version in REQUIRED_PACKAGES.items():
        requirement = f"{package}=={version}"
        check(
            f"requirement {requirement}",
            requirement.lower() in lines,
        )


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
        check(
            f"config.{name} is a positive int",
            isinstance(value, int) and value > 0,
            str(value),
        )

    check(
        "config.MIN_CHARS < config.MAX_CHARS",
        config.MIN_CHARS < config.MAX_CHARS,
        f"{config.MIN_CHARS} < {config.MAX_CHARS}",
    )

    for name in ["ROAST_MODEL", "CHECK_MODEL", "PROMPT_VERSION"]:
        value = getattr(config, name, "")
        check(f"config.{name} is non-empty", bool(value), repr(value))


def check_application_modules() -> None:
    for module_name in ["auth", "storage", "usage"]:
        try:
            __import__(module_name)
            check(f"{module_name}.py imports", True)
        except ImportError as exc:
            check(f"{module_name}.py imports", False, str(exc))


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


def load_local_secrets() -> dict[str, object]:
    secret_path = CHAPTER_ROOT / ".streamlit" / "secrets.toml"
    if not secret_path.exists():
        check(
            "local Streamlit secret exists",
            False,
            "copy secrets.example.toml to secrets.toml",
        )
        return {}

    check("local Streamlit secret exists", True)

    try:
        with secret_path.open("rb") as file:
            values = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        check("local Streamlit secret is valid TOML", False, type(exc).__name__)
        return {}

    check("local Streamlit secret is valid TOML", True)
    return values


def configured_secret(value: object) -> bool:
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    placeholders = {
        "replace-with-your-key",
        "replace-with-your-publishable-key",
        "your_api_key_here",
        "your-supabase-key",
    }
    return len(cleaned) >= 20 and cleaned not in placeholders


def check_secrets(values: dict[str, object]) -> None:
    openai_key = values.get("OPENAI_API_KEY", "")
    supabase_url = values.get("SUPABASE_URL", "")
    supabase_key = values.get("SUPABASE_KEY", "")

    check(
        "OPENAI_API_KEY is configured",
        configured_secret(openai_key),
        "the value is intentionally never printed",
    )

    parsed = urlparse(supabase_url) if isinstance(supabase_url, str) else None
    valid_url = bool(parsed and parsed.scheme == "https" and parsed.netloc)
    check(
        "SUPABASE_URL is a valid HTTPS URL",
        valid_url,
        "the value is intentionally never printed",
    )

    check(
        "SUPABASE_KEY is configured",
        configured_secret(supabase_key),
        "the value is intentionally never printed",
    )


def check_ignore_rules() -> None:
    gitignore = REPOSITORY_ROOT / ".gitignore"
    gitignore_text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    git_patterns = {line.strip() for line in gitignore_text.splitlines()}
    check(
        "Streamlit secret is covered by .gitignore",
        bool(
            {
                "**/.streamlit/secrets.toml",
                ".streamlit/secrets.toml",
            }
            & git_patterns
        ),
    )

    dockerignore = CHAPTER_ROOT / ".dockerignore"
    if not dockerignore.exists():
        check(".dockerignore exists", False)
        return

    check(".dockerignore exists", True)
    docker_patterns = {
        line.strip()
        for line in dockerignore.read_text(encoding="utf-8").splitlines()
    }
    check(
        "Streamlit secrets are excluded from Docker",
        ".streamlit/" in docker_patterns,
    )


def check_secret_leaks(values: dict[str, object]) -> None:
    secret_values = [
        value.strip()
        for name in ["OPENAI_API_KEY", "SUPABASE_KEY"]
        if isinstance((value := values.get(name)), str)
        and len(value.strip()) >= 20
    ]

    excluded_parts = {".git", ".venv", "venv", "env", "__pycache__"}
    text_suffixes = {".py", ".json", ".toml", ".md", ".txt", ".yml", ".yaml"}
    leaked_files: list[str] = []

    for path in CHAPTER_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(CHAPTER_ROOT)
        if excluded_parts.intersection(relative.parts):
            continue
        if relative.as_posix() == ".streamlit/secrets.toml":
            continue
        if path.name not in {"Dockerfile", ".dockerignore"} and path.suffix.lower() not in text_suffixes:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        if any(secret in text for secret in secret_values):
            leaked_files.append(relative.as_posix())

    check(
        "configured keys are absent from repository files",
        not leaked_files,
        "none found" if not leaked_files else f"found in {sorted(leaked_files)}",
    )


def check_deployment_files() -> None:
    dockerfile = CHAPTER_ROOT / "Dockerfile"
    if not dockerfile.exists():
        check("Dockerfile exists", False)
    else:
        check("Dockerfile exists", True)
        text = dockerfile.read_text(encoding="utf-8")
        check("Docker listens on the Vercel PORT", "$PORT" in text)
        check("Docker binds Streamlit to all interfaces", "0.0.0.0" in text)
        check("Docker runs as a non-root user", "USER appuser" in text)
        check("Docker limits uploaded files", "--server.maxUploadSize=4" in text)

    vercel_path = CHAPTER_ROOT / "vercel.json"
    if not vercel_path.exists():
        check("vercel.json exists", False)
        return

    check("vercel.json exists", True)
    try:
        configuration = json.loads(vercel_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        check("vercel.json is valid JSON", False, type(exc).__name__)
        return

    check("vercel.json is valid JSON", True)
    service = configuration.get("services", {}).get("resumeroast", {})
    check("Vercel service uses container runtime", service.get("runtime") == "container")
    check("Vercel service points to Dockerfile", service.get("entrypoint") == "Dockerfile")

    rewrites = configuration.get("rewrites", [])
    routes_to_service = any(
        rewrite.get("source") == "/(.*)"
        and isinstance(rewrite.get("destination"), dict)
        and rewrite["destination"].get("service") == "resumeroast"
        for rewrite in rewrites
        if isinstance(rewrite, dict)
    )
    check("Vercel routes all traffic to ResumeRoast", routes_to_service)


def check_live(values: dict[str, object]) -> None:
    api_key = os.environ.get("OPENAI_API_KEY") or values.get("OPENAI_API_KEY")
    if not configured_secret(api_key):
        check("OPENAI_API_KEY is available for --live", False)
        return

    try:
        import config
        from roast import create_client

        client = create_client(str(api_key))
        response = client.responses.create(
            model=config.CHECK_MODEL,
            instructions="Reply with exactly one word: OK.",
            input="ping",
        )
        check("live OpenAI API call succeeds", bool((response.output_text or "").strip()))
    except Exception as exc:
        check("live OpenAI API call succeeds", False, type(exc).__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="make one minimal billed OpenAI call",
    )
    args = parser.parse_args()

    check_python_version()
    check_imports()
    check_requirements()
    check_config()
    check_application_modules()
    check_agent_contract()

    secrets = load_local_secrets()
    check_secrets(secrets)
    check_ignore_rules()
    check_secret_leaks(secrets)
    check_deployment_files()

    if args.live:
        check_live(secrets)
    else:
        print("[SKIP] live API check -- pass --live to run it (this will cost money)")

    print()
    print(f"{len(CHECKS_PASSED)} passed, {len(CHECKS_FAILED)} failed")
    return 0 if not CHECKS_FAILED else 1


if __name__ == "__main__":
    raise SystemExit(main())
