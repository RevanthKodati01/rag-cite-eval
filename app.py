import streamlit as st
import requests

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="RAG Cite Eval", page_icon="📚", layout="wide")
st.title("📚 RAG Cite Eval")

with st.sidebar:
    k = st.slider("Top-K sources", 1, 10, 5)
    if st.button("Re-index data/raw"):
        r = requests.post(f"{API}/ingest", timeout=600)
        if r.status_code == 200:
            st.success(f"Indexed {r.json()['indexed_chunks']} chunks")
        else:
            st.error(r.text)
st.subheader("Upload file")
uploaded = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])

if uploaded is not None:
    files = {"file": (uploaded.name, uploaded.getvalue())}
    r = requests.post(f"{API}/upload", files=files, timeout=600)
    if r.status_code == 200:
        st.success(f"Uploaded: {uploaded.name}")
    else:
        st.error(r.text)

    if st.button("Index uploaded files"):
        r2 = requests.post(f"{API}/ingest", timeout=600)
        if r2.status_code == 200:
            st.success(f"Indexed {r2.json()['indexed_chunks']} chunks")
        else:
            st.error(r2.text)
st.subheader("Files in data/raw")
rf = requests.get(f"{API}/files", timeout=30)
if rf.status_code == 200:
    st.write(rf.json()["files"])

q = st.text_input("Question")

if st.button("Ask", type="primary") and q.strip():
    r = requests.post(f"{API}/ask", json={"question": q, "k": k}, timeout=600)
    if r.status_code != 200:
        st.error(r.text)
    else:
        data = r.json()
        st.subheader("Answer")
        st.write(data["answer"])

        st.subheader("Sources")
        for s in data["sources"]:
            page = s["page"]
            page_str = f"p.{page}" if isinstance(page, int) and page > 0 else "txt"
            st.markdown(f"**[{s['rank']}] {s['source']} ({page_str}) • chunk {s['chunk']}**")
            st.caption(s["snippet"])
            st.divider()
