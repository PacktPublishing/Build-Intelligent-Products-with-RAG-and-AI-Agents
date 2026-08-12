# Chapter 4: Building the MVP

## What you build

ResumeRoast v1: a Streamlit app where a job seeker uploads a resume PDF and a target role, and gets back a 1–10 score with a brutally specific, section-by-section critique that quotes their actual resume.

## Product version

ResumeRoast v1: Wrapper MVP

The scope contract for this version is [resumeroast-prd.md](resumeroast-prd.md) — a filled-in copy of [prd-template.md](prd-template.md). Read it first; every file below exists to serve one of its eight boxes.

## What this chapter adds

- Streamlit interface
- Core LLM action
- PDF ingestion
- Validation
- CSV data layer
- Grounded prompt
- Smoke tests
- Public deployment

## What is deliberately not included

- **No RAG.** Everything the roast needs (the resume, the role, the model's trained judgment) fits in a single prompt — there's no corpus to retrieve from yet.
- **No vector database.** Same reason: nothing here needs to be *found*, only sent.
- **No agent.** The product only generates text; it doesn't take actions like fetching a job posting (that's Chapter 5).
- **No production database.** Two CSV files are the entire data layer until real users make that untenable (Chapter 6).
- **No real authentication.** Email capture identifies a user across visits; it is not a password and isn't described as one.
- **No OCR.** Scanned/image-only PDFs get a clear refusal message instead of a hallucinated critique.

## Build order

1. Environment and skeleton
2. Core action
3. Input pipeline
4. Data layer
5. Five-node Streamlit journey
6. Prompt hardening
7. Smoke testing
8. Deployment

## Files

| File | Role in the chapter |
|---|---|
| `app.py` | Five-node Streamlit journey |
| `config.py` | Model names and usage limits |
| `roast.py` | Core AI action |
| `prompts.py` | Production system prompt |
| `ingest.py` | PDF extraction and validation |
| `storage.py` | CSV data boundary |
| `scripts/run_core_action.py` | Test the engine without the UI |
| `scripts/run_smoke_tests.py` | Run all five prompt smoke tests |
| `scripts/verify_setup.py` | Confirm the environment is ready, with no API spend |

## Before you begin

- Python 3.11+
- Git
- An OpenAI API key
- $5 of test credit (the manuscript's napkin math puts this chapter's entire cost well under that)
- A virtual environment (instructions below)

## Installation

First, confirm your `python3` actually resolves to 3.11 or later — many machines still default to an older system Python:

```bash
python3 --version
```

If that prints something below 3.11, install a newer Python (from [python.org](https://python.org), `pyenv`, or `brew install python@3.12`) and use that binary — for example `python3.12` — in place of `python3` below.

**macOS / Linux:**

```bash
cd chapter-04-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**

```bat
cd chapter-04-mvp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configure your API key

1. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`.
2. Open it and replace the placeholder with your real OpenAI API key.
3. Never commit `secrets.toml` — the repository's `.gitignore` already excludes it, but double-check before every push.

## Run the core action first

```bash
export OPENAI_API_KEY=sk-...   # Windows: set OPENAI_API_KEY=sk-...
python scripts/run_core_action.py --pdf smoke-tests/duty-lister-resume.pdf --role "Marketing Manager"
```

This deliberately tests the product's uncertain core — whether the prompt produces a roast worth paying for — before wrapping it in a UI. The interface is a solved problem; the prompt is not.

## Run the application

```bash
streamlit run app.py
```

## Follow the five nodes

1. Landing
2. Auth
3. Home
4. Input
5. Output

## Run the smoke tests

```bash
python scripts/run_smoke_tests.py            # dry run, prints what would run, no cost
python scripts/run_smoke_tests.py --live      # real API calls, real (small) cost
```

The dry run (no flags) makes no API calls and costs nothing — it just prints which fixtures and roles would run, so you can sanity-check the mapping for free. Pass `--live` to actually run all five resumes through the model. Results are saved to `smoke-tests/results/`, which is gitignored — read them against the checklist the script prints at the end, and against `smoke-tests/expected-behaviour.md`.

If you change the prompt in response to something a smoke test caught, record it in [prompt-development/prompt-log.md](prompt-development/prompt-log.md) — what failed, what you changed, what happened — so a fix for one fixture doesn't silently regress another.

## Pre-push security audit

Do this **before** you push, not after:

```bash
git status
git diff --cached
git log --all --oneline -- .streamlit/secrets.toml
```

Confirm no `.venv`, no `data/*.csv`, and no `secrets.toml` are staged. If the last command returns anything at all, your key is in Git history — removing the file in a new commit doesn't remove it from history. Revoke that key in your provider dashboard immediately and generate a fresh one.

## Deploy

1. Push this repository — the whole repository you cloned, not just the `chapter-04-mvp` folder on its own — to GitHub (or your fork of it).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Choose **Create app**, pick your repository, the `main` branch, and `chapter-04-mvp/app.py` as the entrypoint. Streamlit Cloud installs from the `requirements.txt` next to that entrypoint, so nothing extra is needed for it to find `chapter-04-mvp/requirements.txt`.
4. Open **Advanced settings** before deploying and paste the contents of your local `secrets.toml` into the Secrets field.
5. Deploy, and watch the build log: environment created, requirements installed, app started.

## Known limitations

- CSV writes are not concurrency-safe.
- CSV persistence may disappear on Streamlit Community Cloud (its filesystem is ephemeral and resets on redeploys).
- Email entry is not real authentication.
- Scanned/image-only PDFs are unsupported.
- Resume feedback is inherently subjective.
- Model names and prices change on the provider's schedule, not this book's.
- `ROAST_MODEL` defaults to a reasoning model, which spends part of its output budget on hidden reasoning before writing the critique. If you swap in a different model, check `config.py`'s comment on `ROAST_REASONING_EFFORT` — reasoning models need it set, non-reasoning models need it set to `None`.
- No rate limiting.
- No durable database (the stack commitment's graduation trigger is Supabase, once strangers are using the live URL regularly — that's Chapter 6's work).
- No production monitoring.

## Done when

- A stranger can open the public URL, enter an email, upload a PDF resume, enter a target role, and receive a grounded critique without any help from you.
- Returning with the same email shows previous roasts, while local persistence remains available.
- Testing for this chapter stays within the intended cost budget (well under $5).

## Next chapter

Chapter 5 gives ResumeRoast an agent layer and job-posting interaction — but only once this MVP has earned it. Nothing about that layer is implemented here.
