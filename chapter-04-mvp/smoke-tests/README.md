# Smoke-test resumes

Five synthetic resumes, each designed to break the prompt in one specific way. All names, companies, and details are fictional. Run them with `scripts/run_smoke_tests.py` (dry run by default; pass `--live` for real, billed API calls).

| File | Suggested target role | What it tests |
|---|---|---|
| `strong-senior-resume.pdf` | Senior Software Engineer | A genuinely strong resume aligned with the role. Does the model manufacture criticism to seem tough, instead of following the "if it's strong, say so briefly and move on" rule? |
| `duty-lister-resume.pdf` | Marketing Manager | Every bullet describes a responsibility, not an outcome. Does the model quote the weak bullets and name the missing impact, per the grounding rules? |
| `career-changer-resume.pdf` | Data Analyst | A solid professional history aimed at a different field. Does the model engage honestly with the relevance gap, rather than substituting generic formatting feedback? |
| `sparse-graduate-resume.pdf` | Software Engineer | Half a page, one internship, no metrics anywhere. Does the model report the missing information, per the "missing sections" rule, instead of inventing it? |
| `mismatched-role-resume.pdf` | Fintech Chief Technology Officer | A credible pastry chef resume aimed at a wildly unrelated target role. Does the roast stay grounded and honest when the premise itself is broken? |

## Why these five

Each fixture targets one of the failure modes the chapter's placeholder prompt showed: generic feedback, inconsistent tone, structural drift, and hallucination. See `expected-behaviour.md` for what a passing run looks like on each one, and `../prompt-development/prompt-log.md` for how to record what you find.
