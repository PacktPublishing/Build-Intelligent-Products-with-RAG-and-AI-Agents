# Expected behaviour

Qualitative expectations for each smoke-test resume. These are not exact scores — model outputs vary run to run, and the point of the grounding rules is consistent *behaviour*, not a fixed number. Read each output against these expectations, and against the review checklist `run_smoke_tests.py` prints at the end of a run.

## `strong-senior-resume.pdf` — Senior Software Engineer

Expect a high score and brief acknowledgement of genuine strengths (the quantified impact in each bullet). The model should **not** invent weaknesses to sound tough — if it manufactures criticism here, the "say so briefly and move on" rule needs a harder edge.

## `duty-lister-resume.pdf` — Marketing Manager

Expect a low-to-mid score. Bullet quality should be the harshest section, with direct quotes of the "Responsible for..." bullets and a clear statement of what outcome is missing from each. Generic advice ("quantify your achievements") should be paired with a specific quote, not floated on its own.

## `career-changer-resume.pdf` — Data Analyst

Expect the "Relevance to role" section to name the gap directly — teaching experience does not map cleanly to a data analyst role — while still crediting the self-directed SQL/Python projects as relevant signal. A passing run treats the gap honestly rather than dodging into formatting nitpicks.

## `sparse-graduate-resume.pdf` — Software Engineer

Expect the model to flag missing metrics and thin experience explicitly ("no measurable outcome is given for the internship") rather than inventing achievements that aren't in the text. This is the missing-sections rule under the most pressure of the five fixtures.

## `mismatched-role-resume.pdf` — Fintech Chief Technology Officer

Expect the model to engage honestly with the mismatch — a strong pastry chef resume does not become a CTO resume — while still critiquing the document on its own terms (bullet quality, structure) rather than refusing to answer or inventing fintech experience that isn't there.
