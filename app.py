import streamlit as st
import requests
from typing import List

API = "http://127.0.0.1:8000"

# 1. CHANGED LAYOUT TO "centered"
st.set_page_config(page_title="RAG Cite Eval", page_icon="📚", layout="centered")

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

# If API is down, stop early
if not api_ok():
    st.error("FastAPI server is not reachable. Start it with:\n\n`uvicorn src.api.server:app --reload --port 8000`")
    st.stop()

# -----------------------------
# Header
# -----------------------------
# Using columns just to push the status indicators to the right side of the header
header_left, header_right = st.columns([3, 1])
with header_left:
    st.title("📚 RAG Cite Eval")
    st.caption("Upload documents → index into a vector DB → ask questions → get **answers with citations**.")
with header_right:
    st.write("API:", "✅ Online" if api_ok() else "❌ Offline")
    st.write("Ollama:", "✅ Running" if ollama_ok() else "⚠️ Not detected")

st.divider()

# -----------------------------
# Main Centered Content
# -----------------------------

# --- SECTION 1: UPLOAD & INDEX ---
st.subheader("📤 1. Upload & Index Documents")

uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"], label_visibility="collapsed")

if uploaded is not None:
    files = {"file": (uploaded.name, uploaded.getvalue())}
    with st.spinner(f"Uploading {uploaded.name}…"):
        r = requests.post(f"{API}/upload", files=files, timeout=600)

    if r.status_code == 200:
        st.success(f"Uploaded: **{uploaded.name}**")
    else:
        st.error(r.text)

# Action Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("⚡ Index Files", use_container_width=True):
        ingest_now()
with col2:
    if st.button("🔁 Re-index All", use_container_width=True):
        ingest_now()
with col3:
    if st.button("📦 Refresh List", use_container_width=True):
        st.rerun()

# Show current files
with st.expander("📁 View Indexed Files"):
    files = get_files()
    if not files:
        st.info("No files found. Upload a document to get started.")
    else:
        st.write(f"**{len(files)} file(s)** indexed:")
        for f in files:
            st.markdown(f"- `{f}`")

st.divider()

# --- SECTION 2: CHAT & QUERY ---
st.subheader("💬 2. Ask a Question")

# Advanced Settings (Hidden by default in an expander to keep UI clean)
with st.expander("⚙️ Advanced Settings"):
    k = st.slider("Top-K sources to retrieve", 1, 10, 5)

demo_questions = [
    "— Select a quick demo question —",
    "Summarize the document in 5 bullet points with citations.",
    "List the key events in chronological order with citations.",
    "Who is the main character and what is their goal? Cite evidence.",
    "What is the central conflict/problem? Support with citations.",
    "Give 3 important quotes and explain each with citations."
]

demo_pick = st.selectbox("Quick demo questions (optional)", demo_questions, label_visibility="collapsed")

if "q" not in st.session_state:
    st.session_state.q = ""

if demo_pick != "— Select a quick demo question —":
    st.session_state.q = demo_pick

q = st.text_input("Question", value=st.session_state.q, placeholder="Ask something grounded in the uploaded documents…", label_visibility="collapsed")

if st.button("Ask Question", type="primary", use_container_width=True):
    if q.strip():
        with st.spinner("Retrieving sources and generating a cited answer…"):
            r = requests.post(f"{API}/ask", json={"question": q, "k": k}, timeout=600)

        if r.status_code != 200:
            st.error(r.text)
        else:
            data = r.json()

            st.markdown("### ✅ Answer")
            st.info(data.get("answer", ""))

            st.markdown("### 📌 Sources Used")
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
    else:
         st.warning("Please enter a question first.")