# Chapter 5 smoke tests

This folder carries forward the five fictional Chapter 4 resumes and now supports two separate questions:

1. **Is the final roast still good?** Run `scripts/run_smoke_tests.py`.
2. **Did the agent take the right path?** Run `scripts/run_agent_smoke_tests.py`.

Both commands are free dry runs by default. Pass `--live` to make real, billed model calls. Live JSON output is written to the gitignored `results/` directory.

## Output-quality regression fixtures

| File | Generic intent | What it protects |
|---|---|---|
| `strong-senior-resume.pdf` | Senior Software Engineer | Does not manufacture criticism |
| `duty-lister-resume.pdf` | Marketing Manager | Quotes weak duty bullets and names missing impact |
| `career-changer-resume.pdf` | Data Analyst | Handles a genuine relevance gap honestly |
| `sparse-graduate-resume.pdf` | Software Engineer | Reports missing evidence instead of inventing it |
| `mismatched-role-resume.pdf` | Fintech CTO | Stays grounded under an absurd mismatch |

Generic role strings should not call either tool. That is now part of the regression.

## Agent trajectory cases

The agent suite uses `duty-lister-resume.pdf` for every case and injects fixed tool observations so the route — not the public web — is under test.

| Case | Expected action path |
|---|---|
| `direct-hit` | `fetch_webpage` exactly once, then final roast |
| `ambiguous-intent` | `search_company_culture` exactly once, then final roast |
| `broken-premise` | failed `fetch_webpage` exactly once, no retry, exact safe exit phrase, no roast |
| `distraction` | `fetch_webpage` exactly once, detect recipe, return mandated exit phrase |

```bash
python scripts/run_agent_smoke_tests.py
python scripts/run_agent_smoke_tests.py --live
python scripts/run_agent_smoke_tests.py --live --case distraction
```

Automatic checks verify tool names, call counts, and required failure phrases. A human must still read the final critiques for grounding, tone, and usefulness.
