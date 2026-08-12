"""ResumeRoast v1 -- the five-node journey from Chapter 2, in Streamlit.

Node 1: LANDING
Node 2: AUTH
Node 3: HOME
Node 4: INPUT
Node 5: OUTPUT

Each node below is one stage of that journey, in order, with no
branches back to an earlier node. The comments are the same five names
as the journey map -- this file's structure is that map, transcribed.
"""

import re

import streamlit as st

from config import MAX_PAGES
from ingest import IngestError, extract_resume_text
from roast import RoastError, create_client, is_resume, parse_score, roast_resume
from storage import get_roasts, save_roast, save_user

MAX_ROLE_CHARS = 100
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

st.set_page_config(page_title="ResumeRoast", page_icon="🔥")


@st.cache_resource
def _client():
    """Create the OpenAI client once per app process, from Streamlit secrets."""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None
    if not api_key:
        return None
    return create_client(api_key)


client = _client()

# ---- Node 1: LANDING ----
st.title("ResumeRoast 🔥")
st.subheader(
    "Find out exactly what a recruiter thinks of your resume - "
    "before you send it. Brutal, specific, instant."
)

if client is None:
    st.error(
        "This app is missing its OPENAI_API_KEY secret. If you're running "
        "locally, copy .streamlit/secrets.example.toml to "
        ".streamlit/secrets.toml and add your key."
    )
    st.stop()

# ---- Node 2: AUTH ----
if "email" not in st.session_state:
    email_input = st.text_input("Your email to get started:")
    st.caption("This just associates your roasts with you -- it isn't a password.")
    if st.button("Start roasting"):
        if _EMAIL_RE.match(email_input.strip()):
            st.session_state.email = email_input.strip().lower()
            save_user(st.session_state.email)
            st.rerun()
        else:
            st.warning("Please enter a valid email address.")
    st.stop()

st.caption(f"Signed in as **{st.session_state.email}**")
if st.button("Use another email / start over"):
    del st.session_state["email"]
    st.rerun()

# ---- Node 3: HOME ----
history = get_roasts(st.session_state.email)
if history:
    st.write(f"You have **{len(history)}** previous roast(s).")
    for record in reversed(history):
        label = (
            f"{record['target_role']} - scored {record['score']}/10 "
            f"on {record['created_at'][:10]}"
        )
        with st.expander(label):
            st.markdown(record["roast_text"])
else:
    st.info("No roasts yet -- upload your resume below to get your first one.")

# ---- Node 4: INPUT ----
st.divider()
uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
role = st.text_input(
    "Target role (e.g., Senior Data Analyst)",
    max_chars=MAX_ROLE_CHARS,
)
st.caption(f"PDF only, up to {MAX_PAGES} pages.")

role_clean = role.strip()

# ---- Node 5: OUTPUT ----
if uploaded and role_clean and st.button("Roast it 🔥"):
    try:
        with st.spinner("Reading your resume..."):
            text = extract_resume_text(uploaded)
            if not is_resume(client, text):
                st.error(
                    "That doesn't look like a resume. Please upload your "
                    "actual resume as a PDF."
                )
                st.stop()

        with st.spinner(f"Roasting against '{role_clean}' expectations..."):
            result = roast_resume(client, text, role_clean)

        score = parse_score(result)
        save_roast(st.session_state.email, role_clean, score, result)
        st.markdown(result)

    except IngestError as exc:
        st.error(str(exc))
    except RoastError as exc:
        st.error(str(exc))
    except Exception:
        st.error("Something went wrong on our end. Please try again in a moment.")
elif uploaded and not role_clean:
    st.warning("Please enter a target role before roasting.")
