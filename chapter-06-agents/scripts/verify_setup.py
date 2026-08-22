#!/usr/bin/env python3
"""Verify the Chapter 6 RAG plus agent project without making an API call."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def check(label: str, passed: bool, detail: str = "") -> bool:
    print(f"[{'PASS' if passed else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    return passed


def main() -> int:
    passed = []
    passed.append(check("Python 3.11+", sys.version_info >= (3, 11), sys.version.split()[0]))
    for module in ("streamlit", "openai", "pypdf", "requests", "bs4"):
        try:
            __import__(module)
            passed.append(check(f"import {module}", True))
        except ImportError as exc:
            passed.append(check(f"import {module}", False, str(exc)))
    try:
        import config
        from corpus import load_rubrics

        corpus = load_rubrics(ROOT / config.CORPUS_PATH)
        passed.append(check("rubric corpus loads", bool(corpus), f"{len(corpus)} chunks"))
        passed.append(check("embedding model configured", bool(config.EMBEDDING_MODEL), config.EMBEDDING_MODEL))
        passed.append(check("agent step cap configured", isinstance(config.MAX_AGENT_STEPS, int) and config.MAX_AGENT_STEPS > 0, str(config.MAX_AGENT_STEPS)))
        threshold = getattr(config, "MIN_RETRIEVAL_SCORE", None)
        passed.append(check("retrieval threshold is between 0 and 1", isinstance(threshold, float) and 0 < threshold < 1, str(threshold)))
    except Exception as exc:
        passed.append(check("rubric corpus loads", False, str(exc)))
    print(f"\n{sum(passed)} passed, {len(passed) - sum(passed)} failed")
    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
