# Expected behaviour

These five expectations remain the Chapter 4 output-quality baseline. In Chapter 5, each generic role must also produce an empty tool-call trajectory.

The four new agent expectations are:

- **Direct hit:** one `fetch_webpage` call with the exact supplied URL, followed by a job-specific scored roast.
- **Ambiguous intent:** one `search_company_culture` call with the named company, followed by a company-aware scored roast.
- **Broken premise:** one failed fetch, zero retries, and exactly `I couldn't access that link. Please check it and try again.` No score, headings, or generic roast may follow.
- **Distraction:** one fetch, zero retries, and a response beginning `This URL doesn't look like a job board.`

Qualitative expectations for each smoke-test resume. These are not exact scores. Model outputs vary run to run, and the point of the grounding rules is consistent *behaviour*, not a fixed number. Read each output against these expectations and against the review checklist `run_smoke_tests.py` prints at the end of a run.

## `strong-senior-resume.pdf`: Senior Software Engineer

Expect a high score and brief acknowledgement of genuine strengths (the quantified impact in each bullet). The model should **not** invent weaknesses to sound tough. If it manufactures criticism here, the "say so briefly and move on" rule needs a harder edge.

## `duty-lister-resume.pdf`: Marketing Manager

Expect a low-to-mid score. Bullet quality should be the harshest section, with direct quotes of the "Responsible for..." bullets and a clear statement of what outcome is missing from each. Generic advice ("quantify your achievements") should be paired with a specific quote, not floated on its own.

## `career-changer-resume.pdf`: Data Analyst

Expect the "Relevance to role" section to name the gap directly. Teaching experience does not map cleanly to a data analyst role, while the self-directed SQL/Python projects remain relevant signal. A passing run treats the gap honestly rather than dodging into formatting nitpicks.

## `sparse-graduate-resume.pdf`: Software Engineer

Expect the model to flag missing metrics and thin experience explicitly ("no measurable outcome is given for the internship") rather than inventing achievements that aren't in the text. This is the missing-sections rule under the most pressure of the five fixtures.

## `mismatched-role-resume.pdf`: Fintech Chief Technology Officer

Expect the model to engage honestly with the mismatch. A strong pastry chef resume does not become a CTO resume, while the document can still be critiqued on its own terms (bullet quality, structure) rather than refused or padded with invented fintech experience.
