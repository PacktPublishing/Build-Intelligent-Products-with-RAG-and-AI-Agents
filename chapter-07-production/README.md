# Chapter 7: Shipping It

This directory turns the Chapter 5 RAG layer and Chapter 6 agent layer into a small, deployable ResumeRoast product. It adds Supabase authentication, Row Level Security, durable history, an atomic daily allowance, a Docker runtime, and GitHub Actions checks.

This is a learning deployment for a small group of real users. It is not a claim that the product is ready for unlimited public traffic.

## What you need

- Python 3.11 or later
- An OpenAI API key for the supplied example
- A Supabase project
- A GitHub repository you control
- A Vercel account for the hosted path

The architecture is provider-neutral. The example uses OpenAI because the prior chapters use its SDK, while retrieval, authentication, and deployment boundaries do not depend on it.

## 1. Configure local secrets

From this directory, copy the example file:

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and provide these values:

```toml
OPENAI_API_KEY = "..."
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-publishable-key"
```

Find the URL and publishable key in Supabase under **Project Settings > API**. Use the publishable key, not a service-role key. The application relies on the signed-in user session and Row Level Security to constrain access.

`.streamlit/secrets.toml` is ignored by Git. Never commit it.

## 2. Create the database boundary

In the Supabase SQL Editor, run the complete migration at:

```text
supabase/migrations/001_initial_schema.sql
```

It creates the `roasts` and `daily_usage` tables, their Row Level Security policies, and the `consume_daily_request()` function.

For the first book walkthrough, disable **Confirm Email** in **Authentication > Providers > Email**. This lets a new password sign-up return a session immediately. It is a workshop choice, not a public-launch recommendation. If you enable confirmation later, configure the Site URL, redirect URLs, and a reliable email delivery path before relying on it.

## 3. Run locally

Create and activate a virtual environment, then install the requirements:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the checks before opening the app:

```bash
python scripts/verify_setup.py
python -m unittest discover -s tests -v
```

Start Streamlit:

```bash
python -m streamlit run app.py
```

Create two disposable accounts and use a synthetic resume. Generate one roast as the first account. Sign in as the second account and verify that it cannot see the first account's history. That proves a filter did not accidentally become your authorization boundary.

The default allowance is three requests per user per UTC day. Do not make paid calls only to exhaust it. The important outcome is that the next request is rejected before a model call after the allowance is used.

## 4. Push a safe commit and check CI

From the repository root, make sure no real secret file is staged:

```bash
git status --short --ignored --untracked-files=all -- chapter-07-production/.streamlit
git add chapter-07-production
git diff --cached --check
git commit -m "Add Chapter 7 production build"
git push
```

GitHub Actions runs the repository-safe verifier and offline tests. It intentionally does not use a model-provider key or call live APIs.

## 5. Deploy to Vercel

Import your GitHub repository in Vercel. When prompted for a root directory, select:

```text
chapter-07-production
```

The supplied `Dockerfile` and `vercel.json` define the container deployment. Add these three environment variables for the Production environment:

```text
OPENAI_API_KEY
SUPABASE_URL
SUPABASE_KEY
```

Deploy, wait for the deployment to report **Ready**, and open its generated HTTPS URL. Do this before adding a custom domain. A generated URL proves that the product works independently of DNS and branding.

## 6. Smoke test the public URL

Open the generated URL in a private browser window. Create a new disposable account, upload a synthetic resume, and generate one roast. Confirm that retrieved evidence appears with the result, sign out and back in to confirm history is durable, then use a second account to confirm the first account's history is not visible.

If the build fails, first check that the Vercel root directory is `chapter-07-production`. If the app reports a missing setting, compare the exact environment-variable names above and redeploy. If sign-up succeeds without a session, revisit the Confirm Email choice described earlier.
