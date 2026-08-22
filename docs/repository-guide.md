# Repository guide

## Chapter folder naming

Chapter folders are named `chapter-NN-<short-name>`, for example `chapter-04-mvp`. The number matches the book chapter; the short name is a one-or-two-word label for the product version that chapter ships (`mvp`, `agent`, and so on).

## Running a chapter

Each chapter folder is self-contained: its own `requirements.txt`, its own README with exact setup and run commands, its own way of verifying the build works (a terminal script, smoke tests, or a formal test suite, whichever that chapter's manuscript teaches). You should never need files from another chapter folder to run one chapter. Start with that chapter's README.

## Why chapter snapshots are self-contained

Readers enter this repository at different points — some read straight through, some jump to the chapter they're currently on. A chapter folder that depended on a later chapter's code, or that got silently rewritten when a later chapter shipped, would break that second group. Self-containment is what makes "start here" in the root README true.

## Why later chapters don't overwrite earlier code

`chapter-04-mvp` should still run, unmodified, after `chapter-07-production` exists. If Chapter 7 changes storage.py's internals, that change lives in `chapter-07-production/storage.py`, not by editing the Chapter 4 copy in place. This is more duplication than a single evolving codebase would have, and that's an intentional trade: a reader on Chapter 4 should never see Chapter 7's database code by accident.

## What belongs in `shared/`

Only assets that are genuinely identical across multiple chapters and unlikely to diverge — for example, a smoke-test document that later chapters reuse without modification. `shared/` is not a place to move Chapter 4's application code to avoid duplicating a few lines. See [shared/README.md](../shared/README.md).

## What must remain chapter-local

Application code (`app.py`, `config.py`, `roast.py`, `ingest.py`, `storage.py`, `prompts.py`), chapter-specific scripts and smoke tests, and anything that expresses that chapter's particular architecture decisions.

## Adding a new chapter

1. Copy the previous chapter's working product as the starting point.
2. Rename the folder for the new chapter (`chapter-05-agent`, etc.).
3. Leave the previous chapter's folder unchanged.
4. Add a "What changed from the previous chapter?" section to the new chapter's README.
5. Update the root README's chapter table.
6. Add only the capabilities the corresponding manuscript actually introduces.
7. Keep the new chapter independently runnable — don't reach into a sibling chapter folder.
8. Verify the newly introduced behaviour the way that chapter's manuscript verifies it (a terminal script, a smoke test, a formal test suite — only add the last of these if the manuscript actually teaches it).
9. Don't retroactively add the new chapter's architecture to older chapter snapshots.
10. Document any migration or breaking change clearly in the new chapter's CHANGELOG.
