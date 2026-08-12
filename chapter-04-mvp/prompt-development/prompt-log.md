# Prompt iteration log

Record every prompt change here: what failed, what you changed, and what happened. Prompt edits interact — a fix for one fixture can quietly regress another — so this log is how you notice. It's also the seed of the prompt-versioning discipline Chapter 8 builds properly.

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

## Illustrative entry 1 (template — not a real run)

## Version
placeholder → v1, draft 1

## Date
_fill in when you run this_

## Fixture
`duty-lister-resume.pdf`

## Failure observed
The placeholder prompt's critique was generic — "consider quantifying your achievements" — and never quoted the actual weak bullets, so it read the same as feedback for any other resume.

## Prompt change
Added the grounding rule requiring every criticism to quote or directly reference specific resume text before critiquing it (the "quote, then critique" rule in `# GROUNDING RULES`).

## Expected result
Bullet-quality criticism should now open with an actual quoted bullet from the resume, followed by what's missing from it.

## Actual result
_Run `scripts/run_smoke_tests.py --live --fixture duty-lister-resume.pdf` and record what you see here._

## Regression check
_Re-run `strong-senior-resume.pdf` after this change to confirm it didn't start manufacturing criticism on a resume that doesn't need it._

---

## Illustrative entry 2 (template — not a real run)

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
