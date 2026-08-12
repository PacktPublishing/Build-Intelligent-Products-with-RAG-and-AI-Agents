# ResumeRoast v1 — one-page PRD

## 1. One-liner

It scores and critiques a resume for job seekers so they can understand exactly what's holding them back from getting interviews.

## 2. User

Active job seekers, mid-application-cycle, who have sent out applications and heard silence, and don't know why.

## 3. Problem evidence

- Competitor gap: existing tools are keyword-mechanical; human coaches cost $100+ and take days.
- Interview signal: "brutal" came up unprompted in three of five interviews; repeated phrase "I have no idea if it's even good."
- Demand: live waitlist signups, r/resumes posting volume, rising search trends.

## 4. Core action

User uploads a resume PDF and a target role; receives a 1-10 score and a brutally specific, section-by-section critique that quotes their actual resume.

## 5. The five nodes

- **Landing:** hook and one call to action.
- **Auth:** email capture to associate roasts with a person.
- **Home:** list of previous roasts, or a prompt to run the first one.
- **Input:** PDF upload plus a target role text field.
- **Output:** score, section-by-section roast, rendered on screen and saved.

## 6. Stack commitment

A wrapper, because a strong model with the resume and role in context produces the critique the interviews demanded. Split model tiers: frontier for the roast, budget for input checking, both in config variables. Data starts as CSV, graduating to Supabase when strangers use the live URL. No vector layer until the role-rubric corpus outgrows the prompt. One roast costs about $0.024 at frontier pricing, capped by upload validation, an output token limit, and no history accumulation.

## 7. Out of scope

Resume rewriting. Cover letter generation. LinkedIn profile analysis. Comparing against a specific job posting URL (that's Chapter 5's agent feature, and it will be earned there). Payment. Real authentication with passwords. PDF export of the roast. Multiple resume versions per user. Any admin dashboard.

## 8. Done when

A stranger can upload a resume on a live URL and get a roast that quotes their actual bullets, without any help from me. Returning with the same email shows previous roasts. Total spend for the chapter stays under $5.
