# Grounded smoke tests

These three synthetic resumes are copied from Chapter 4 so the Chapter 5 project can run independently. They remain fictional examples.

| Fixture | Target role | Expected first-party evidence |
|---|---|---|
| `duty-lister-resume.pdf` | Marketing Manager | `MKT-01` |
| `career-changer-resume.pdf` | Senior Data Analyst | `DA-01` |
| `strong-senior-resume.pdf` | Senior Software Engineer | `SWE-01` |

Run `python scripts/run_grounded_smoke_tests.py` for a free contract check, then add `--live` to make the embedding and generation calls. Review the saved JSON output manually. A passing source ID does not prove the generated prose is faithful to that source or the resume.
