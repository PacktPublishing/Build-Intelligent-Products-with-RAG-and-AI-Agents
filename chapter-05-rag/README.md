# Chapter 5: Grounding Your Product with RAG

## What you build

ResumeRoast v1.5: the Chapter 4 MVP, now grounded in a small curated library of role-specific recruiter rubrics. At startup, the app embeds that small stable library once. For each roast, it embeds the target role, retrieves the most relevant rubric chunks, and passes those labeled chunks to the roast prompt.

This is deliberately modest RAG. The corpus is a transparent JSON file, retrieval happens in memory, and the generated feedback shows which rubric IDs it used. That is enough to learn the product boundary: retrieve facts or standards the model does not reliably carry in the prompt, then constrain the answer to that evidence.

## Architecture

```text
resume PDF -> validation -> budget resume check
target role -> embedding -> local cosine retrieval -> labeled rubric evidence
                                                   |
resume + role + evidence ------------------------> grounded roast -> CSV history
```

## Start here

Run these commands from `chapter-05-rag`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
python scripts/verify_setup.py
python -m unittest discover -s tests -v
python scripts/run_retrieval_checks.py
python scripts/run_grounded_smoke_tests.py
python -m streamlit run app.py
```

Replace the placeholder in `.streamlit/secrets.toml` with your own API key. Do not commit that file.

## What to evaluate

Run retrieval and answer checks separately:

```bash
python scripts/run_retrieval_checks.py --live
python scripts/run_grounded_smoke_tests.py --live
```

For each target role, inspect whether the returned rubric IDs make sense before judging the final feedback. The grounded smoke-test runner saves the output and source IDs for three synthetic resumes. Inspect whether the roast names the retrieved rubric IDs only where it uses them, stays grounded in the actual resume, and does not treat the rubric as a live job description.

## Why no vector database yet?

The corpus is tiny, static, and read by one local app process. Storing embeddings in a database would add operational work without solving a current problem. Chapter 7 moves product data into Supabase when real usage requires it; the same retrieval boundary can then move to pgvector without changing the rest of the application.

## Known limits

- Embeddings and generation are hosted API calls and can change in model availability, price, or behavior.
- The rubric corpus is an illustrative product asset, not a universal hiring standard or a live job posting.
- The rubric library is embedded once per running app process. A restart rebuilds it. Persisted embeddings are an earned production upgrade, not a prerequisite for this chapter.
- The retrieval score threshold is a conservative starting point, not a universal truth. Calibrate it against your saved retrieval cases before changing the user-facing fallback.
- Retrieval quality and answer quality are different. A fluent roast can still be grounded in the wrong rubric.
- CSV persistence, real authentication, monitoring, and durable production infrastructure remain Chapter 7 work.

## Next chapter

Chapter 6 adds a capped, read-only agent only after ResumeRoast can give grounded feedback from its own product knowledge.
