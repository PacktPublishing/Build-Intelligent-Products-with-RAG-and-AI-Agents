# Contributing

This repository is the code companion to a specific book, so contributions are welcome within a specific shape.

## Ground rules

- Keep code aligned with the chapter it lives in. A chapter folder should match what its manuscript describes, not what you'd prefer to build instead.
- Do not introduce a future chapter's features into an earlier chapter's snapshot (no agent code in `chapter-04-mvp`, no database code before the chapter that adds one, and so on).
- Open an issue before proposing a large architecture change, so it can be discussed against the book's intent before you invest time in it.
- Verify any behaviour change by re-running the chapter's own checks (its core-action script, smoke tests, or setup verifier). Only add a formal automated test suite to a chapter if that chapter's manuscript actually teaches one — this repo follows the book's testing story, not a separate one.
- Never commit real resumes, other real personal data, or API keys — synthetic fixtures only.
- Preserve beginner readability. This code is read by people learning the pattern, not just running it.
- Keep chapter folders independently runnable. A fix in one chapter should not require touching another.
- If you change a file path or command, update the README that references it in the same PR.

## Adding a new chapter

See [docs/repository-guide.md](docs/repository-guide.md) for the full checklist.

## Reporting security issues

See [SECURITY.md](SECURITY.md) — do not open a public issue for an exposed key or credential.
