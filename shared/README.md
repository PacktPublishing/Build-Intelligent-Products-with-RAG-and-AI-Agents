# shared

This directory holds assets genuinely reused, unchanged, across multiple chapter folders — not a place to move chapter code to avoid duplicating a few lines.

- Application code lives inside its chapter snapshot (`chapter-04-mvp/`, and later chapter folders), never here.
- A self-contained chapter is more valuable to a reader than deduplicating a handful of files, so duplication across chapters is expected and fine.
- Future smoke-test documents or fixtures may move here, or be copied here, only once a later chapter genuinely reuses them unmodified. Until that's true, they stay in the chapter that owns them.

See [test-assets/README.md](test-assets/README.md) for what belongs specifically in that subdirectory.
