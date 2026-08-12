# Security

## If you leak an API key

1. **Do not** open a public GitHub issue describing the leak or including the key.
2. Revoke the key immediately in your model provider's dashboard. Bots scan public repositories for leaked keys continuously; assume it will be found and used within minutes.
3. Generate a replacement key and store it only in your local, untracked secrets file (or your deployment platform's secrets manager).
4. Remove the secret from Git history using an appropriate history-rewriting tool (for example `git filter-repo`), not just a new commit that deletes the file — the old commit still contains the key until history is rewritten.
5. Rotate any other credential that might have been exposed alongside it.

## User data

- Resumes uploaded by users may contain personal information (names, contact details, employment history).
- Chapter 4's CSV storage is a local, testing-stage data layer. It has no encryption, access control, or retention policy.
- Do not commit `data/*.csv`, uploaded PDFs, or any other file containing real user data to this repository.
- Production-grade privacy, retention, and access-control decisions are out of scope for Chapter 4 and are addressed as part of the production-hardening work in later chapters.

## Reporting a vulnerability

Open a private security advisory on the repository's GitHub page, or contact the maintainer directly rather than filing a public issue.
