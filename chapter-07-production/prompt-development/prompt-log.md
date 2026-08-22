# Prompt iteration log

Record every prompt change here: what failed, what you changed, and what happened. Prompt edits interact. A fix for one fixture can quietly regress another, so this log is how you notice. It's also the seed of the prompt-versioning discipline Chapter 8 builds properly.

Each entry:

```
## Version
## Date
## Fixture
## Failure observed
## Prompt change
## Expected result
## Actual result
## Regression check
```

---

## Illustrative entry 1 (template, not a real run)

## Version
placeholder → v1, draft 1

## Date
_fill in when you run this_

## Fixture
`duty-lister-resume.pdf`

## Failure observed
The placeholder prompt's critique was generic: "consider quantifying your achievements". It never quoted the actual weak bullets, so it read the same as feedback for any other resume.

## Prompt change
Added the grounding rule requiring every criticism to quote or directly reference specific resume text before critiquing it (the "quote, then critique" rule in `# GROUNDING RULES`).

## Expected result
Bullet-quality criticism should now open with an actual quoted bullet from the resume, followed by what's missing from it.

## Actual result
_Run `scripts/run_smoke_tests.py --live --fixture duty-lister-resume.pdf` and record what you see here._

## Regression check
_Re-run `strong-senior-resume.pdf` after this change to confirm it didn't start manufacturing criticism on a resume that doesn't need it._

---

## Illustrative entry 2 (template, not a real run)

## Version
v1 draft 1 → v1 draft 2

## Date
_fill in when you run this_

## Fixture
`strong-senior-resume.pdf`

## Failure observed
An earlier draft of the grounding rules didn't say what to do when a resume was genuinely strong, so the model sometimes invented minor criticisms to avoid sounding like it had nothing to say.

## Prompt change
Added the explicit rule: "If the resume seems strong on a dimension, say so briefly and move on. Do not manufacture criticism to seem tough."

## Expected result
Strong dimensions get a short acknowledgement instead of manufactured nitpicks.

## Actual result
_Record what you see here._

## Regression check
_Re-run `duty-lister-resume.pdf` and `sparse-graduate-resume.pdf` to confirm the model didn't get generally softer._

---

Add your own entries below as you iterate.

---

## v1 -> v2-agent (implementation baseline)

## Date

2026-08-06

## Fixture

All four Chapter 5 trajectory cases.

## Failure observed

The Chapter 4 prompt had no vocabulary for tools, no routing policy, no definition of irrelevant tool output, and no instruction to stop after a textual tool error.

## Prompt change

Added the sixth `# TOOL GUARDRAILS` layer and expanded grounding so resume text and tool observations are both untrusted data.

## Expected result

URLs use the scraper once; company-only intents use company search once; generic roles use no tool; failed or irrelevant observations terminate without retry.

## Actual result

Run `scripts/run_agent_smoke_tests.py --live` and record the model/version-specific outcome here.

## Regression check

Run `scripts/run_smoke_tests.py --live` to confirm all five Chapter 4 resume-quality fixtures still meet their original expectations.

---

## v2-agent -> v2-agent.1

## Date

2026-08-06

## Fixture

`broken-premise`

## Failure observed

The agent selected `fetch_webpage`, received a deterministic `404 Not Found` observation, and correctly avoided a retry. It then violated the intended stop condition by producing a complete `SCORE: 3/10` generic roast and merely adding "Please share a working link" inside the relevance section.

## Prompt change

Made the tool-guardrail layer explicitly override the scored-output contract. Added exact, non-roast exit phrases for webpage and company-search errors and explicitly prohibited scores, headings, and resume feedback after a tool error.

## Expected result

After one failed webpage fetch, the next response is exactly: `I couldn't access that link. Please check it and try again.` No tool retry and no roast follow.

## Actual result

Pending the next live run of `python scripts/run_agent_smoke_tests.py --live --case broken-premise`.

## Regression check

All 11 offline unit tests pass, including a new test that accepts the exact safe exit and rejects the previously observed scored-roast response. The 24 no-cost setup checks and agent smoke-test dry run also pass. Re-run the paid Chapter 4 quality suite after the live broken-premise check passes.

---

## v2-agent.1 -> v2-agent.2

## Date

2026-08-06

## Fixture

Apple Careers Data Engineer URL (`200657330-3543`).

## Failure observed

The URL returned HTTP 200 with the correct Apple Careers title and metadata, but the agent replied that it did not look like a job board. Apple's complete job record lived inside `window.__staticRouterHydrationData`; `fetch_webpage` deleted every script before extraction and exposed only global navigation and legal text to the model.

## Prompt change

Added a distinct incomplete-job-page guardrail and changed the irrelevant-page wording from “job board” to “job posting.” The scraper change, rather than the prompt, does the primary repair: it extracts standard Schema.org `JobPosting` JSON-LD and Apple's data-only hydration payload before deleting scripts.

## Expected result

The Apple URL yields the actual title, description, responsibilities, and qualifications and proceeds to a grounded roast. Other recognizable job pages that cannot be read ask the user to paste the job description. Recipe and other irrelevant pages still stop with the exact non-job-posting response.

## Actual result

All 15 offline unit tests pass, including dedicated Schema.org, Apple hydration, incomplete-job-page, and exact irrelevant-page regressions. A live scraper verification against the reported Apple URL returned 3,651 characters of real job content with every expected field and no tool warning or error.

## Regression check

The original visible-HTML extraction, private-address block, capped agent loop, exact broken-link response, and deterministic trajectory checks remain covered and passing.
