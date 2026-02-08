import streamlit as st
import requests
from typing import List

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="RAG Cite Eval", page_icon="📚", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
def api_ok() -> bool:
    try:
        r = requests.get(f"{API}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def ollama_ok() -> bool:
    # best-effort: if Ollama isn't installed or running, this will fail
    try:
        r = requests.get("http://localhost:11434", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def get_files() -> List[str]:
    try:
        r = requests.get(f"{API}/files", timeout=10)
        if r.status_code == 200:
            return r.json().get("files", [])
    except Exception:
        pass
    return []

def ingest_now():
    with st.spinner("Indexing documents… (this may take a bit)"):
        r = requests.post(f"{API}/ingest", timeout=600)
    if r.status_code == 200:
        st.success(f"Indexed **{r.json()['indexed_chunks']}** chunks")
    else:
        st.error(r.text)

# -----------------------------
# Header
# -----------------------------
st.title("📚 RAG Cite Eval")
st.caption("Upload documents → index into a vector DB → ask questions → get **answers with citations**.")

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.subheader("Settings")
    k = st.slider("Top-K sources", 1, 10, 5)

    st.subheader("Status")
    st.write("API:", "✅ Online" if api_ok() else "❌ Offline")
    st.write("Ollama:", "✅ Running" if ollama_ok() else "⚠️ Not detected")

    st.divider()
    if st.button("🔁 Re-index data/raw", use_container_width=True):
        ingest_now()

# If API is down, stop early (better UX)
if not api_ok():
    st.error("FastAPI server is not reachable. Start it with:\n\n`uvicorn src.api.server:app --reload --port 8000`")
    st.stop()

# -----------------------------
# Layout: left (upload/index), right (ask/answer)
# -----------------------------
left, right = st.columns([0.9, 1.1], gap="large")

with left:
    st.subheader("📤 Upload")
    uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])

    if uploaded is not None:
        files = {"file": (uploaded.name, uploaded.getvalue())}
        with st.spinner(f"Uploading {uploaded.name}…"):
            r = requests.post(f"{API}/upload", files=files, timeout=600)

        if r.status_code == 200:
            st.success(f"Uploaded: **{uploaded.name}**")
        else:
            st.error(r.text)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("⚡ Index uploaded files", use_container_width=True):
            ingest_now()

    with col_b:
        if st.button("📦 Refresh file list", use_container_width=True):
            st.rerun()

    st.divider()

    st.subheader("📁 Indexed files")
    files = get_files()
    if not files:
        st.info("No files found in `data/raw/` yet. Upload a PDF/TXT to get started.")
    else:
        st.write(f"**{len(files)} file(s)** in `data/raw/`")
        for f in files:
            st.markdown(f"- `{f}`")

with right:
    st.subheader("💬 Ask a question")

    demo_questions = [
        "Summarize the document in 5 bullet points with citations.",
        "List the key events in chronological order with citations.",
        "Who is the main character and what is their goal? Cite evidence.",
        "What is the central conflict/problem? Support with citations.",
        "Give 3 important quotes and explain each with citations."
    ]

    demo_pick = st.selectbox("Quick demo questions (optional)", ["— Select one —"] + demo_questions)

    if "q" not in st.session_state:
        st.session_state.q = ""

    if demo_pick != "— Select one —":
        st.session_state.q = demo_pick

    q = st.text_input("Question", value=st.session_state.q, placeholder="Ask something grounded in the uploaded documents…")

    ask_col1, ask_col2 = st.columns([0.25, 0.75])
    with ask_col1:
        ask_clicked = st.button("Ask", type="primary", use_container_width=True)

    with ask_col2:
        st.caption("Tip: Questions that request **evidence** and **citations** show the power of RAG.")

    if ask_clicked and q.strip():
        with st.spinner("Retrieving sources and generating a cited answer…"):
            r = requests.post(f"{API}/ask", json={"question": q, "k": k}, timeout=600)

        if r.status_code != 200:
            st.error(r.text)
        else:
            data = r.json()

            st.markdown("### ✅ Answer")
            st.write(data.get("answer", ""))

            st.markdown("### 📌 Sources")
            sources = data.get("sources", [])
            if not sources:
                st.warning("No sources returned. Try re-indexing or asking a more specific question.")
            else:
                for s in sources:
                    page = s.get("page")
                    page_str = f"p.{page}" if isinstance(page, int) and page > 0 else "txt"
                    title = f"[{s.get('rank')}] {s.get('source')} ({page_str}) • chunk {s.get('chunk')}"
                    with st.expander(title, expanded=(s.get("rank") == 1)):
                        st.write(s.get("snippet", ""))
