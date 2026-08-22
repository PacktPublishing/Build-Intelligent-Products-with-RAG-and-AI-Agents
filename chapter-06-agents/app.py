"""ResumeRoast v2: Chapter 5 RAG plus a bounded, read-only agent."""

import re

import streamlit as st

from config import CORPUS_PATH, MAX_INTENT_CHARS, MAX_PAGES
from corpus import load_rubrics
from ingest import IngestError, extract_resume_text
from retrieval import RetrievalError, build_index
from roast import RoastError, create_client, is_resume, parse_score, roast_resume
from storage import get_roasts, save_roast, save_user

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
st.set_page_config(page_title="ResumeRoast", page_icon="🔥")


@st.cache_resource
def get_client():
    try:
        key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        key = None
    return create_client(key) if key else None


@st.cache_data
def get_corpus():
    return load_rubrics(CORPUS_PATH)


@st.cache_resource
def get_rubric_index(api_key: str):
    return build_index(create_client(api_key), get_corpus())


client = get_client()
st.title("ResumeRoast 🔥")
st.subheader("Grounded resume feedback with bounded public-context tools when they are useful.")
if client is None:
    st.error("This app needs an OPENAI_API_KEY in .streamlit/secrets.toml.")
    st.stop()

try:
    rubric_index = get_rubric_index(st.secrets.get("OPENAI_API_KEY"))
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
for record in reversed(get_roasts(st.session_state.email)):
    with st.expander(f"{record['target_role']} - scored {record['score']}/10"):
        st.markdown(record["roast_text"])
        st.caption(f"Rubrics used: {record['evidence_ids']}")

st.divider()
with st.form("roast_form", clear_on_submit=False):
    uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    intent = st.text_area("What are you applying for?", placeholder="Paste a job URL, name a company, or describe the role...", max_chars=MAX_INTENT_CHARS)
    st.caption(f"PDF only, up to {MAX_PAGES} pages. The app retrieves curated role expectations before it considers public tools.")
    submitted = st.form_submit_button("Roast it 🔥", type="primary")

if submitted:
    if uploaded is None:
        st.warning("Upload your resume before roasting.")
    elif not intent.strip():
        st.warning("Tell me what you are applying for before roasting.")
    else:
        try:
            resume_text = extract_resume_text(uploaded)
            if not is_resume(client, resume_text):
                st.error("That does not look like a resume. Please upload your actual resume as a PDF.")
                st.stop()
            with st.spinner("Retrieving role evidence and checking public context when needed..."):
                result = roast_resume(client, resume_text, intent.strip(), rubric_index)
            if result.text.startswith("SCORE:"):
                score = parse_score(result.text)
                evidence_ids = ", ".join(match.chunk.chunk_id for match in result.evidence)
                save_roast(st.session_state.email, intent.strip(), score, result.text, evidence_ids)
                st.markdown(result.text)
                st.caption(f"Grounded in curated rubric chunks: {evidence_ids}")
                with st.expander("Agent trace"):
                    st.json(result.trace)
            else:
                st.warning(result.text)
        except (IngestError, RoastError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("Something went wrong on our end. Please try again shortly.")
