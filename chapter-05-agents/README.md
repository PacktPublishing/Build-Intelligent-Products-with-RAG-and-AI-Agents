# Chapter 5: Adding the Agent Layer

## What you build

ResumeRoast v2: the Chapter 4 product, extended with a small read-only agent. A user uploads a resume and writes one messy intent — a role, a company, or a job URL. The model chooses whether to scrape a page, search for company context, or proceed without a tool, then returns the same grounded roast.

## What changed from Chapter 4?

Everything that already worked remains: the five-node Streamlit journey, PDF validation, budget-tier resume gate, frontier-tier roast, CSV boundary, score contract, history, and synthetic resumes.

Chapter 5 changes only the earned capability:

- `app.py` replaces the rigid target-role field with one open-ended text area.
- `roast.py` replaces the one-shot wrapper call with a Responses API tool loop capped at three model steps.
- `tool_schemas.py` defines the two-item JSON menu the model sees.
- `tools.py` implements the two read-only Python tools.
- `prompts.py` adds the sixth prompt layer: tool routing, relevance, error, fallback, and read-only guardrails.
- `scripts/run_agent_smoke_tests.py` evaluates the action trajectory, not only the final prose.
- Saved roasts use `user_intent` instead of `target_role`; each chapter has its own data directory, so Chapter 4 data is untouched.

## Product version

ResumeRoast v2: Capped read-only agent

The scope contract is [resumeroast-prd.md](resumeroast-prd.md).

## Architecture

```text
resume PDF -> validate -> budget resume check
                         |
open intent ------------>+-> capped agent loop (max 3 model calls)
                              |-- fetch_webpage(url)
                              |-- search_company_culture(company_name)
                              `-- no tool for a generic role
                                      |
                                  final roast -> CSV history
```

The model never executes Python. It emits a `function_call` item; `roast.py` validates the name and arguments, calls a function from `tools.py`, then sends a `function_call_output` observation back to the model. The loop keeps the full Responses API output items in its next input, as required for multi-step reasoning.

## Safety boundaries

- **Read-only tools only.** There is no email, application submission, payment, database-write, or browser-control tool.
- **Hard step cap.** `MAX_AGENT_STEPS = 3` ends the run even if the model keeps asking for tools.
- **Text errors.** Tools return `Tool Error: ...` observations instead of crashing the loop.
- **Strict schemas.** Both JSON schemas reject extra properties.
- **One call at a time.** Parallel tool calls are disabled so trajectories remain bounded and easy to audit.
- **Public web only.** The scraper rejects non-HTTP schemes, credentials in URLs, private/local/reserved IP addresses, and redirects to them.
- **Bounded inputs.** Resume text, intent length, tool text, redirects, network time, and model output are capped in `config.py`.
- **Untrusted observations.** The system prompt treats resume text and scraped/search text as data, never instructions.
- **Data-only structured extraction.** The scraper reads Schema.org `JobPosting` JSON-LD and Apple's server-rendered hydration payload without executing JavaScript.

## Files

| File | Role |
|---|---|
| `app.py` | Five-node Streamlit journey with the open intent field |
| `config.py` | Models and all usage/network caps |
| `roast.py` | Resume gate, capped agent loop, tool dispatcher, score parser |
| `tool_schemas.py` | Strict JSON tool menu shown to the model |
| `tools.py` | Read-only scraper and company search implementations |
| `prompts.py` | Six-layer agent system prompt |
| `ingest.py` | Unchanged PDF validation boundary from Chapter 4 |
| `storage.py` | CSV boundary, evolved from target role to user intent |
| `scripts/run_core_action.py` | Run one real agent request without Streamlit |
| `scripts/run_smoke_tests.py` | Re-run the five Chapter 4 output-quality regressions |
| `scripts/run_agent_smoke_tests.py` | Run the four Chapter 5 trajectory cases |
| `scripts/verify_setup.py` | Free environment and contract checks |
| `tests/` | Offline unit tests for caps, dispatch, schemas, and network safety |

## Quick start for newcomers

You need Python 3.11 or later, Git, and your own OpenAI API key with API billing or credits available. Create and manage keys on the [OpenAI API keys page](https://platform.openai.com/api-keys). Do not share a personal key or commit it to Git.

Run every command below from `chapter-05-agents`, not from the repository root.

### Windows PowerShell

```powershell
cd C:\path\to\packt-book\chapter-05-agents
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .streamlit\secrets.example.toml .streamlit\secrets.toml
```

If Windows says `python` is not recognized, use the Python launcher in the first three commands instead: `py -3.11 --version`, `py -3.11 -m venv .venv`, and then the virtual-environment commands shown above. If `py` is also unavailable, install Python 3.11 or later from [python.org](https://www.python.org/downloads/) and enable its launcher during installation.

If PowerShell blocks `Activate.ps1`, do not change your machine-wide execution policy. Use the virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\verify_setup.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS / Linux

```bash
cd /path/to/packt-book/chapter-05-agents
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

### Configure the API key

Open the newly created `.streamlit/secrets.toml` and replace the placeholder:

```toml
OPENAI_API_KEY = "paste-your-own-key-here"
```

Keep the filename exactly `secrets.toml`. The application reads it on the server; it is ignored by Git and must never be uploaded or pasted into an issue, screenshot, source file, notebook, or chat. Each reader should use their own key.

## Verify the installation without API charges

These commands check Python, dependencies, configuration, the local secret format, agent contracts, and offline regressions. They do not contact the OpenAI API unless you explicitly add `--live`.

```bash
python scripts/verify_setup.py
python -m unittest discover -s tests -v
python scripts/run_smoke_tests.py
python scripts/run_agent_smoke_tests.py
```

Expected result: the setup verifier reports no failures, the unit suite ends with `OK`, and both smoke scripts say `Dry run -- no API calls will be made`.

## Run the application

```bash
python -m streamlit run app.py
```

Streamlit prints a local URL, normally `http://localhost:8501`. Open it and follow the five screens:

1. Enter an email. This is only a local history label, not real authentication.
2. Upload a text-based PDF resume of four pages or fewer.
3. Enter a role, company, or job-posting URL.
4. Click the always-visible **Roast it 🔥** button; Ctrl+Enter is not required.
5. Wait for the resume check, optional read-only tool call, and final roast.

Try all three routing shapes:

1. A real job URL, such as an individual posting on a company careers site.
2. A company without a URL: `I want a backend role at Airbnb`.
3. A generic role: `Senior Data Analyst`.

The uploaded PDF is not saved by this chapter, but its extracted text is sent to the OpenAI API for analysis. Roasts and the email label are stored locally under `data/`; those CSV files are ignored by Git.

## Optional: run one agent request from the terminal

Terminal scripts read `OPENAI_API_KEY` from the current shell rather than Streamlit's secrets file. Set it only for the current terminal session, run the command, and remove it afterwards.

**Windows PowerShell:**

```powershell
$secureKey = Read-Host "Paste your OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
python scripts\run_core_action.py --pdf smoke-tests\duty-lister-resume.pdf --intent "I want to work as a backend developer at Airbnb"
Remove-Item Env:OPENAI_API_KEY
```

**macOS / Linux:**

```bash
export OPENAI_API_KEY="$(python -c 'import getpass; print(getpass.getpass("Paste your OpenAI API key: "))')"
python scripts/run_core_action.py \
  --pdf smoke-tests/duty-lister-resume.pdf \
  --intent "I want to work as a backend developer at Airbnb"
unset OPENAI_API_KEY
```

This command makes real, billed model calls. Watch the terminal for the selected action, bounded observation preview, and final response.

## Evaluate the four trajectories

```bash
python scripts/run_agent_smoke_tests.py --live
python scripts/run_agent_smoke_tests.py --live --case broken-premise
```

The live trajectory suite makes real model calls but injects deterministic tool observations. This is deliberate: it tests whether the model chose the right action and stopped correctly without allowing a changed job page, anti-bot response, or search ranking to corrupt the evaluation. Full traces and outputs go to the gitignored `smoke-tests/results/` directory.

The four cases match the manuscript:

| Case | Expected trajectory |
|---|---|
| Direct hit | Exactly one `fetch_webpage` call, then a job-specific roast |
| Ambiguous intent | Exactly one `search_company_culture` call, then a company-aware roast |
| Broken premise | One failed fetch, no retry, then the exact safe exit phrase with no scored roast |
| Distraction | One fetch of recipe text, then the mandated non-job-posting exit phrase |

## Before committing or pushing

Run these commands from `chapter-05-agents`:

```bash
git status --short --ignored
git check-ignore .streamlit/secrets.toml
git log --all -- .streamlit/secrets.toml
```

The secret should appear as ignored, never staged. The final command should print nothing. Also confirm that `.venv/`, `data/*.csv`, `smoke-tests/results/`, and real resumes are not staged. If a real key ever enters a commit or public message, revoke it immediately in the provider dashboard and generate a replacement; deleting it in a later commit is not sufficient.

## Troubleshooting

- **`python` is older than 3.11:** install a current Python release, then recreate `.venv` with that interpreter.
- **PowerShell refuses to activate the environment:** use the direct `.\.venv\Scripts\python.exe ...` commands shown above.
- **`ModuleNotFoundError`:** confirm the virtual environment is active and rerun `python -m pip install -r requirements.txt`.
- **The app says the API key is missing:** confirm the file is exactly `.streamlit/secrets.toml`, the key name is exactly `OPENAI_API_KEY`, and the value is not the placeholder. Restart Streamlit after changing secrets.
- **The button or page looks stale:** stop Streamlit with Ctrl+C, start it again with `python -m streamlit run app.py`, then refresh the browser.
- **The PDF is rejected as empty or scanned:** use a PDF containing selectable text; OCR is outside this chapter's scope.
- **Port 8501 is busy:** run `python -m streamlit run app.py --server.port 8502` and open the URL Streamlit prints.
- **A model is unavailable for your project:** check the model names in `config.py` against the models available to your OpenAI API project. Keep the budget check and frontier roast as separate configuration values.
- **A job page cannot be read:** paste the job description into the intent field, or try another individual posting URL. Some sites block basic HTTP clients.

## Known limitations

- The scraper handles ordinary visible HTML, standard Schema.org `JobPosting` JSON-LD, and Apple's `__staticRouterHydrationData` job payload. It extracts data before removing scripts and never executes JavaScript.
- Some job boards expose neither readable HTML nor supported structured data, or block basic HTTP clients. When page metadata still proves that the URL is a job page, the app asks the user to paste the full description instead of incorrectly calling it a non-job page. Browser automation remains out of scope for this chapter.
- Company search uses DuckDuckGo's HTML results page to avoid adding a second API key. It may be rate-limited or change markup; failure becomes a tool observation.
- Search snippets are public context, not authoritative company policy.
- Tool routing and final prose remain probabilistic; run the trajectory suite after every prompt or model change.
- CSV concurrency, ephemeral Streamlit storage, email-only identification, monitoring, rate limits, and durable infrastructure remain Chapter 6 work.
- There is still no RAG/vector database because this feature has an action gap, not a private-corpus retrieval gap.

## Done when

- Generic roles bypass tools and preserve Chapter 4 output quality.
- URLs route to `fetch_webpage`; company-only intents route to `search_company_culture`.
- Broken and irrelevant resources stop without retrying or inventing context.
- The loop cannot exceed three model calls.
- All offline tests pass and all four live trajectories pass manual review.

The tool-loop structure follows the official [OpenAI function-calling guide](https://developers.openai.com/api/docs/guides/function-calling): preserve response output items, execute each function call in application code, and return a `function_call_output` linked by `call_id`.
