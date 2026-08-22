"""ResumeRoast v1.5: the Chapter 4 MVP with a visible RAG step."""

import re

import streamlit as st

from config import CORPUS_PATH, MAX_PAGES, MAX_ROLE_CHARS
from corpus import load_rubrics
from ingest import IngestError, extract_resume_text
from roast import RoastError, create_client, is_resume, parse_score, roast_resume
from retrieval import RetrievalError, build_index
from storage import get_roasts, save_roast, save_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

st.set_page_config(page_title="ResumeRoast", page_icon="🔥")


@st.cache_resource
def get_client():
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None
    return create_client(api_key) if api_key else None


@st.cache_data
def get_corpus():
    return load_rubrics(CORPUS_PATH)


@st.cache_resource
def get_rubric_index(api_key: str):
    """Build once per app process, not once per user roast."""
    client = create_client(api_key)
    return build_index(client, get_corpus())


client = get_client()
st.title("ResumeRoast 🔥")
st.subheader("Specific resume feedback, now grounded in the expectations of your target role.")

if client is None:
    st.error("This app needs an OPENAI_API_KEY in .streamlit/secrets.toml.")
    st.stop()

try:
    api_key = st.secrets.get("OPENAI_API_KEY")
    rubric_index = get_rubric_index(api_key)
except (ValueError, RetrievalError) as exc:
    st.error(str(exc))
    st.stop()

if "email" not in st.session_state:
    email = st.text_input("Your email to get started:")
    st.caption("This is a history label, not a password.")
    if st.button("Start roasting"):
        if EMAIL_RE.match(email.strip()):
            st.session_state.email = email.strip().lower()
            save_user(st.session_state.email)
            st.rerun()
        st.warning("Please enter a valid email address.")
    st.stop()

st.caption(f"Signed in as **{st.session_state.email}**")
history = get_roasts(st.session_state.email)
for record in reversed(history):
    with st.expander(f"{record['target_role']} - scored {record['score']}/10"):
        st.markdown(record["roast_text"])
        st.caption(f"Rubrics used: {record['evidence_ids']}")

st.divider()
uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
role = st.text_input("Target role", max_chars=MAX_ROLE_CHARS, placeholder="Senior Data Analyst")
st.caption(f"PDF only, up to {MAX_PAGES} pages. The app searches its curated rubric library for this role.")

if uploaded and role.strip() and st.button("Roast it 🔥"):
    try:
        with st.spinner("Reading your resume..."):
            resume_text = extract_resume_text(uploaded)
            if not is_resume(client, resume_text):
                st.error("That does not look like a resume. Please upload your actual resume as a PDF.")
                st.stop()
        with st.spinner("Finding the most relevant role expectations..."):
            result = roast_resume(client, resume_text, role.strip(), rubric_index)
        score = parse_score(result.text)
        evidence_ids = ", ".join(match.chunk.chunk_id for match in result.evidence)
        save_roast(st.session_state.email, role.strip(), score, result.text, evidence_ids)
        st.markdown(result.text)
        st.caption(f"Grounded in curated rubric chunks: {evidence_ids}")
    except (IngestError, RoastError) as exc:
        st.error(str(exc))
    except Exception:
        st.error("Something went wrong on our end. Please try again shortly.")
elif uploaded and not role.strip():
    st.warning("Please enter a target role before roasting.")
