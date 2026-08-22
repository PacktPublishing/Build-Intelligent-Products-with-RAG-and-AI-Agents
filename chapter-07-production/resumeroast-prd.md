# ResumeRoast v2: agent-layer PRD

## 1. One-liner

It scores and critiques a resume against the role, company, or live job posting a job seeker actually cares about so they can fix the gaps most likely to cost that application.

## 2. User

Active job seekers with a specific application or target company who want evidence-based feedback before they submit.

## 3. Problem evidence

- Chapter 4 proved the wrapper can produce a useful grounded roast.
- The highest-value follow-up is comparison with a specific live posting.
- A live URL and current company context are outside the model's prompt desk, proving an action gap.

## 4. Core action

The user uploads a resume and describes what they are applying for; a capped read-only agent gathers only the missing public context and returns a grounded 1 to 10 critique.

## 5. The five nodes

- **Landing:** same promise and one call to action.
- **Auth:** same email capture boundary.
- **Home:** same saved-roast history, now labeled by user intent.
- **Input:** PDF upload plus one open-ended intent area.
- **Output:** trajectory runs, final roast is rendered and valid scored outputs are saved.

## 6. Stack commitment

Plain Python and Streamlit remain. OpenAI is called directly through the Responses API. The agent has exactly two read-only tools and at most three model steps. CSV remains until Chapter 7. No vector layer is added because the gap is a live action, not a private knowledge corpus.

## 7. Out of scope

Applying for jobs, sending email, editing a resume, cover letters, payments, write access to external systems, browser automation, RAG, a vector database, durable production storage, real authentication, and automated production observability.

## 8. Done when

The four manuscript trajectories choose the correct tool, use the correct argument, do not retry failed/irrelevant resources, and stop inside the hard cap while generic roles still meet the Chapter 4 roast-quality bar.
