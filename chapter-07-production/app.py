"""ResumeRoast production journey with Supabase authentication.

Node 1: LANDING
Node 2: AUTH
Node 3: HOME
Node 4: INPUT
Node 5: OUTPUT
"""
import os
import streamlit as st

from auth import (
    AuthError,
    create_supabase_client,
    sign_in,
    sign_out,
    sign_up,
)
from config import CORPUS_PATH, MAX_INTENT_CHARS, MAX_PAGES
from corpus import load_rubrics
from ingest import IngestError, extract_resume_text
from roast import (
    RoastError,
    create_client,
    is_resume,
    parse_score,
    roast_resume,
)
from retrieval import RetrievalError, build_index
from storage import StorageError, get_roasts, save_roast
from usage import UsageError, consume_daily_request


st.set_page_config(page_title="ResumeRoast", page_icon="🔥")


def _get_setting(name: str) -> str:
    """Read production environment variables, then local Streamlit secrets."""

    value = os.getenv(name, "").strip()
    if value:
        return value

    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


@st.cache_resource
def _openai_client():
    """Create one reusable OpenAI client for the application process."""

    api_key = _get_setting("OPENAI_API_KEY")

    if not api_key:
        return None

    return create_client(api_key)


def _supabase_client():
    """Return a Supabase client belonging only to this browser session."""

    if "_supabase_client" not in st.session_state:
        st.session_state["_supabase_client"] = create_supabase_client(
            _get_setting("SUPABASE_URL"),
            _get_setting("SUPABASE_KEY"),
        )

    return st.session_state["_supabase_client"]


@st.cache_data
def _rubrics():
    return load_rubrics(CORPUS_PATH)


@st.cache_resource
def _rubric_index(api_key: str):
    return build_index(create_client(api_key), _rubrics())


def _remember_user(user) -> None:
    """Store only the identity fields needed by the interface."""

    st.session_state["auth_user"] = {
        "id": user.id,
        "email": user.email,
    }


openai_client = _openai_client()


# ---- Node 1: LANDING ----
st.title("ResumeRoast 🔥")
st.subheader(
    "Find out exactly what a recruiter thinks of your resume - "
    "before you send it. Brutal, specific, instant."
)

if openai_client is None:
    st.error(
        "This app is missing OPENAI_API_KEY. Configure it as an "
        "environment variable or in .streamlit/secrets.toml."
    )
    st.stop()

try:
    supabase = _supabase_client()
except AuthError as exc:
    st.error(f"Supabase configuration error: {exc}")
    st.stop()

try:
    rubric_index = _rubric_index(_get_setting("OPENAI_API_KEY"))
except (RetrievalError, ValueError) as exc:
    st.error(str(exc))
    st.stop()


# ---- Node 2: AUTH ----
if "auth_user" not in st.session_state:
    st.write(
        "Create an account to save your roast history, "
        "or sign in if you already have one."
    )

    sign_in_tab, sign_up_tab = st.tabs(["Sign in", "Create account"])

    with sign_in_tab:
        with st.form("sign_in_form"):
            login_email = st.text_input(
                "Email",
                key="login_email",
            )
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )
            login_submitted = st.form_submit_button(
                "Sign in",
                type="primary",
            )

        if login_submitted:
            try:
                user = sign_in(
                    supabase,
                    login_email,
                    login_password,
                )
                _remember_user(user)
                st.rerun()
            except AuthError as exc:
                st.error(str(exc))

    with sign_up_tab:
        with st.form("sign_up_form"):
            signup_email = st.text_input(
                "Email",
                key="signup_email",
            )
            signup_password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
                help="Use at least 8 characters.",
            )
            signup_password_again = st.text_input(
                "Confirm password",
                type="password",
                key="signup_password_again",
            )
            signup_submitted = st.form_submit_button(
                "Create account",
                type="primary",
            )

        if signup_submitted:
            if signup_password != signup_password_again:
                st.error("The passwords do not match.")
            else:
                try:
                    user = sign_up(
                        supabase,
                        signup_email,
                        signup_password,
                    )
                    _remember_user(user)
                    st.rerun()
                except AuthError as exc:
                    st.error(str(exc))

    st.stop()


authenticated_user = st.session_state["auth_user"]
user_email = authenticated_user["email"]

st.caption(f"Signed in as **{user_email}**")

if st.button("Sign out"):
    try:
        sign_out(supabase)
    except AuthError as exc:
        st.error(str(exc))
    else:
        st.session_state.pop("auth_user", None)
        st.session_state.pop("_supabase_client", None)
        st.rerun()


# ---- Node 3: HOME ----
# This still reads Chapter 5's local CSV storage. We will replace it
# with authenticated Supabase storage in the next checkpoint.
try:
    history = get_roasts(
        supabase,
        authenticated_user["id"],
    )
except StorageError as exc:
    st.error(str(exc))
    st.stop()

if history:
    st.write(f"You have **{len(history)}** previous roast(s).")

    for record in reversed(history):
        label = (
            f"{record['user_intent']}: scored {record['score']}/10 "
            f"on {record['created_at'][:10]}"
        )

        with st.expander(label):
            st.markdown(record["roast_text"])
else:
    st.info(
        "No roasts yet. Upload your resume below to get your first one."
    )


# ---- Node 4: INPUT ----
st.divider()

with st.form("roast_form", clear_on_submit=False):
    uploaded = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
    )
    user_intent = st.text_area(
        "What are you applying for?",
        placeholder=(
            "Paste a job URL, name a company, "
            "or describe the role..."
        ),
        max_chars=MAX_INTENT_CHARS,
    )
    st.caption(f"PDF only, up to {MAX_PAGES} pages.")
    roast_submitted = st.form_submit_button(
        "Roast it 🔥",
        type="primary",
    )

intent_clean = user_intent.strip()


# ---- Node 5: OUTPUT ----
if roast_submitted:
    if uploaded is None:
        st.warning("Upload your resume before roasting.")
    elif not intent_clean:
        st.warning(
            "Tell me what you are applying for before roasting."
        )
    else:
        try:

            # Local PDF extraction does not spend OpenAI tokens.
            with st.spinner("Reading your resume..."):
                resume_text = extract_resume_text(uploaded)

            # Atomically reserve usage before the first paid model call.
            usage = consume_daily_request(supabase)

            if not usage.allowed:
                st.error(
                    f"You have used all {usage.daily_limit} "
                    "ResumeRoast requests for today. "
                    "Your allowance resets at 00:00 UTC."
                )
                st.stop()

            st.caption(
                f"Daily usage: {usage.used_count}/{usage.daily_limit}: "
                f"{usage.remaining_count} remaining after this request."
            )

            with st.spinner("Checking that the upload is a resume..."):
                if not is_resume(openai_client, resume_text):
                    st.error(
                        "That doesn't look like a resume. "
                        "Please upload your actual resume as a PDF."
                    )
                    st.stop()

            with st.spinner("Retrieving role evidence and analyzing your target..."):
                result = roast_resume(
                    openai_client,
                    resume_text,
                    intent_clean,
                    rubric_index,
                )

            if result.text.startswith("SCORE:"):
                score = parse_score(result.text)

                # Always show the generated result, even if storage is unavailable.
                st.markdown(result.text)
                evidence_ids = ", ".join(match.chunk.chunk_id for match in result.evidence)
                st.caption(f"Grounded in curated rubric chunks: {evidence_ids}")
                with st.expander("Agent trace"):
                    st.json(result.trace)

                try:
                    save_roast(
                        client=supabase,
                        user_id=authenticated_user["id"],
                        user_intent=intent_clean,
                        score=score,
                        roast_text=result.text,
                    )
                except StorageError as exc:
                    st.warning(str(exc))
            else:
                st.warning(result.text)

        except IngestError as exc:
            st.error(str(exc))
        except RoastError as exc:
            st.error(str(exc))
        except UsageError as exc:
            st.error(str(exc))
        except Exception:
            st.error(
                "Something went wrong on our end. "
                "Please try again in a moment."
            )
