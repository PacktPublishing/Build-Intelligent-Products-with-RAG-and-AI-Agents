# ResumeRoast v2 agent system prompt

The executable prompt lives in `../prompts.py` as `AGENT_SYSTEM_PROMPT`. Treat that constant as the authoritative copy. This file explains the six layers and records the behavioural contract readers should evaluate.

## The six layers

| Layer | Job |
|---|---|
| Role | Keeps the senior-recruiter persona and screening standard from Chapter 4 |
| Rubric | Evaluates first impression, bullets, target relevance, career story, and cuts |
| Grounding rules | Binds claims to the resume or a real tool observation and treats both as untrusted data |
| Output contract | Preserves the `SCORE: n/10` line, six headings, and exactly three priority changes |
| Tone | Direct about the document without being cruel about the person |
| Tool guardrails | Overrides the normal roast contract for routing failures, relevance failures, and read-only boundaries |

## Tool guardrails

The exact rules in `prompts.py` require the model to:

1. Route URLs to `fetch_webpage`, company-only intents to `search_company_culture`, and generic roles to no tool.
2. Stop with the dedicated incomplete-page phrase when metadata identifies a job page but the description cannot be extracted; do not mislabel the URL as irrelevant.
3. Stop with the mandated non-job-posting phrase when fetched content is genuinely irrelevant; do not emit a score or critique.
4. Never retry after an observation beginning with `Tool Error:`. A failed webpage fetch and a failed company search each have an exact, non-roast exit phrase.
5. Fall back to a general critique when neither tool applies.
6. Never claim to write, send, submit, purchase, or otherwise mutate an external system.

The guardrail layer explicitly overrides the normal scored-output contract. Without that priority, a model can correctly acknowledge a failed tool and then still produce a generic roast, which is a failed trajectory.

## Why the grounding layer changed

Chapter 4 had one untrusted source: the resume. Chapter 5 has two: the resume and public tool output. A webpage can contain prompt injection just as easily as a PDF, so the v2 rule explicitly treats both as data rather than instructions.

## Synchronization check

After editing the prompt, run:

```bash
python -m unittest discover -s tests -v
python scripts/run_smoke_tests.py --live
python scripts/run_agent_smoke_tests.py --live
```

Record the observed failure, prompt change, expected result, actual result, and regression check in `prompt-log.md`.
