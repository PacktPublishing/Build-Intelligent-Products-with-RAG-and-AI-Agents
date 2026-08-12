# Build Intelligent Products with RAG and AI Agents

This is the official companion code repository for *Build Intelligent Products with RAG and AI Agents*, by Hari Prasad Renganathan. The repository follows a single product, **ResumeRoast**, as it evolves chapter by chapter from a weekend MVP into a production AI product. Each build chapter has its own independently runnable snapshot of ResumeRoast, so you can follow the book sequentially or drop in at whichever chapter you're currently reading.

## Find your chapter

| Chapter | Product version | What changes | Code |
|---|---|---|---|
| Chapter 4 | ResumeRoast v1 | LLM wrapper, Streamlit, PDF ingestion, CSV storage | [chapter-04-mvp](chapter-04-mvp/) |
| Chapter 5 | ResumeRoast v2 | Capped agent loop and read-only job-context tools | [chapter-05-agents](chapter-05-agents/) |
| Chapter 6 | ResumeRoast v3 | Production infrastructure | Coming later |
| Chapter 7 | ResumeRoast v4 | First-user and distribution support | Coming later |
| Chapter 8 | ResumeRoast v5 | Evaluation and iteration | Coming later |
| Chapter 9 | ResumeRoast v6 | Scaling into a real product | Coming later |

## How the repository is organised

Every chapter folder (`chapter-NN-name/`) is a complete, runnable snapshot of ResumeRoast as it exists at the end of that chapter. Later chapters build on the product state of earlier ones, but they do not overwrite the earlier chapter's code — `chapter-04-mvp` will still run exactly as written after Chapter 5's folder is added. The `shared/` directory holds only the small number of assets that are genuinely reused, unchanged, across chapters; it is never a home for active business logic. Chapter folders stay runnable on their own even if something in `shared/` changes later.

## Start here

- **Reading Chapter 4 right now:** open [chapter-04-mvp](chapter-04-mvp/) and follow its README.
- **Reading Chapter 5 right now:** open [chapter-05-agents](chapter-05-agents/), read "What changed from Chapter 4?", then run its no-cost verification commands.
- **Following the book from the beginning:** work through Chapters 1–3 first (design and validation, no code yet), then come back here when the build begins.
- **Joining in a later chapter:** open that chapter's folder, read its README, and check its "What changed from the previous chapter" section before touching code.

## Requirements

- Python 3.11 or later
- Git
- A GitHub account
- An account with an LLM provider (OpenAI in the book's worked examples)
- Chapter-specific requirements are listed inside each chapter folder

## Security

- Never commit API keys.
- Never commit user-generated resume data or any other real personal data.
- Use the example secrets file (`secrets.example.toml`) as your template, and keep your real `secrets.toml` local and untracked.
- If a key ever enters Git history, revoke it in your provider dashboard immediately — removing the file from a later commit does not remove it from history.

## Model and pricing note

Model names, SDK interfaces, prices, and platform limits change on schedules the provider controls, not this book. The model names in the manuscript and in this code reflect what was current at the time of writing. Every model name in this repository lives in a config variable specifically so that a provider change is a one-line edit, not a rewrite. Verify current model availability and pricing in your provider's official documentation before you build.

## Repository status

- **Chapters 4 and 5 — available.** ResumeRoast v1 is in [chapter-04-mvp](chapter-04-mvp/); the independently runnable v2 agent snapshot is in [chapter-05-agents](chapter-05-agents/).
- **Chapters 6–9 — forthcoming.** Their folders will be added as the corresponding manuscripts are finalized.
