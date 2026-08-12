# ResumeRoast v1

## Added

- Core frontier-model roast (`roast.py`)
- Budget-model resume gate (`is_resume`, guarding the frontier call)
- PDF extraction and validation (`ingest.py`)
- Input caps: max pages, min/max characters, max output tokens (`config.py`)
- CSV-backed users and roasts (`storage.py`)
- Five-node Streamlit journey: Landing, Auth, Home, Input, Output (`app.py`)
- Production grounding prompt with all five anatomy layers (`prompts.py`)
- Five synthetic smoke-test fixtures targeting specific failure modes
- Terminal scripts for the core action, setup verification, and smoke testing
- Streamlit Community Cloud deployment instructions

## Fixed

- `roast_resume` now sets `reasoning={"effort": "low"}` on the frontier call. `gpt-5` is a reasoning model: at the default effort, it was spending the entire `MAX_OUTPUT_TOKENS` budget on hidden reasoning tokens for a prompt this detailed, returning an empty `output_text` every time. Only caught by running the smoke tests live against the real API, not by reading the code.
- That reasoning parameter is now only sent when `config.ROAST_REASONING_EFFORT` is set, since non-reasoning models (e.g. `gpt-4o-mini`) reject it outright. Swapping `ROAST_MODEL` for a different tier stays a one-line `config.py` edit, as intended.

## Deferred

- Job-posting URL / agent layer (Chapter 5)
- RAG / vector database (only if a role-rubric corpus outgrows the prompt)
- Supabase as the durable database (Chapter 6, per the stack commitment's graduation trigger)
- Real authentication (Chapter 6)
- Production hardening: monitoring, rate limits, CI/CD (Chapter 6)
- Evaluation and analytics (Chapter 8)
