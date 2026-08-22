# Chapter 6: Adding the Agent Layer

This project extends `chapter-05-rag`. ResumeRoast still retrieves labeled, curated rubric evidence before generation. It now adds two capped, read-only public-web tools when the user's intent earns them.

```text
resume PDF -> validation -> curated-rubric retrieval
user intent -> agent routing -> optional read-only tool observation
resume + evidence + observation -> grounded roast -> CSV history
```

## Start here

Run from `chapter-06-agents`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
python scripts/verify_setup.py
python -m unittest discover -s tests -v
python scripts/run_retrieval_checks.py
python scripts/run_grounded_smoke_tests.py
python scripts/run_agent_smoke_tests.py
python -m streamlit run app.py
```

The supplied implementation uses OpenAI APIs. The architecture does not require that provider: keep generation, embedding, and tool-calling provider code behind the same boundaries if you substitute another service.

## Safety boundaries

- Retrieval runs before the agent, so the critique retains visible curated evidence.
- `fetch_webpage` and `search_company_culture` are read-only.
- The agent has a hard `MAX_AGENT_STEPS` cap and disables parallel tool calls.
- Tool failures become observations, then the prompt requires exact safe exits.
- The app does not claim to send, edit, apply, purchase, or write to any external system.

## Evaluation

Run retrieval quality, grounded-output quality, and agent trajectories separately:

```bash
python scripts/run_retrieval_checks.py --live
python scripts/run_grounded_smoke_tests.py --live
python scripts/run_agent_smoke_tests.py --live
```

The first two checks validate the Chapter 5 RAG layer. The final command uses deterministic fake tool outputs to isolate routing and stopping behavior from live websites.

## Known limits

- Embeddings, generation, and optional live trajectory tests are hosted API calls.
- The in-memory corpus index is right for this tiny curated corpus, not a production vector store.
- CSV persistence, authentication, monitoring, and durable infrastructure are Chapter 7 work.
