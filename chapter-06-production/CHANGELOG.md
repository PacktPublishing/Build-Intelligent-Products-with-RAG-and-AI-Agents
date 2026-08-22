# ResumeRoast v2

## Added

- Two strict, read-only tool schemas: `fetch_webpage` and `search_company_culture`
- Physical tool implementations with the text-error pattern
- Public-network URL validation and redirect revalidation for the scraper
- Responses API ReAct loop with a hard three-step cap
- Terminal-visible action/observation traces plus a structured trace hook
- Sixth prompt layer for routing, relevance, error handling, fallback, and read-only boundaries
- Four deterministic trajectory smoke tests
- Offline unit tests for dispatch, cap enforcement, schemas, text extraction, and private-address blocking

## Changed from v1

- The target-role text input is now one open-ended user-intent text area.
- The one-shot `roast_resume` core action is now `run_agentic_roast`.
- Saved roast records use `user_intent` instead of `target_role`.
- Prompt version moved from `v1` to `v2-agent.2`.
- Requirements add `requests` and `beautifulsoup4`.

## Fixed

- Broken-resource trajectories now explicitly override the scored-roast output contract. A failed webpage fetch returns one exact safe exit phrase, with no generic fallback roast, and the smoke test asserts that complete response rather than looking for one keyword.
- Job extraction now reads Schema.org `JobPosting` JSON-LD and Apple's server-rendered router hydration data before script removal. This fixes valid Apple Careers URLs being mistaken for irrelevant pages.
- Recognized job pages whose descriptions remain unreadable now return a distinct paste-the-description response instead of the misleading non-job-page response.
- The resume uploader and intent field now use a Streamlit form with an always-visible submit button, so text-area edits are submitted by clicking `Roast it` rather than requiring Ctrl+Enter first.
- Newcomer setup now has separate PowerShell and macOS/Linux quick starts, one-key security guidance, expected verification output, first-run UI steps, pre-push checks, and troubleshooting. The setup verifier validates the local Streamlit secret and ignore rule without printing the credential.

## Preserved

- Five-node Streamlit journey
- Explicit OpenAI client creation outside module import
- Budget-tier resume validation before the frontier call
- PDF ingestion and size caps
- Score parser and grounded output contract
- CSV storage boundary and local history
- Chapter 4 synthetic resume fixtures and quality regression suite

## Deferred

- Browser automation for job boards that expose neither readable nor supported structured data
- Write-capable tools and human approval flows
- RAG/vector storage
- Durable database, real authentication, monitoring, rate limiting, and production cost controls (Chapter 6)
