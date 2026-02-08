# rag-cite-eval# RAG-CITE-EVAL 🔎📄✅
A lightweight **Retrieval-Augmented Generation (RAG)** app that answers questions over your documents **with citations** — plus a simple evaluation harness to check citation grounding.

**Stack:** Streamlit + FastAPI + ChromaDB + Sentence-Transformers + PyMuPDF + Ollama (local LLM)

---

## What this project does
1. **Ingest** PDFs/TXT from `data/raw/`
2. **Chunk** text into overlapping passages
3. **Embed + index** chunks into a persistent Chroma vector database (`data/processed/chroma/`)
4. For a question:
   - **Retrieve** top-K relevant chunks
   - Ask an LLM to answer using **inline citations** like `[1] [2]`
5. Includes an **eval runner** (`eval_set.jsonl`) to sanity-check grounding.

---

## Why it matters
Many RAG demos answer without proof. This project forces **citation-first** responses so users can verify claims fast, and provides a basic eval script to measure whether answers and citations align.

---

## Features
- ✅ Upload PDFs/TXT and index them
- ✅ Ask questions and get answers with citations (`[1]`, `[2]`, etc.)
- ✅ View retrieved source snippets + metadata (file, page, chunk)
- ✅ Persistent vector store (ChromaDB)
- ✅ Simple evaluation runner over a JSONL eval set

---

## Demo (add later)
> Add screenshots or a short GIF here once your UI is polished.

Suggested:
- `screenshots/ui_home.png`
- `screenshots/answer_with_sources.png`

---

## Quickstart (Local)

### 0) Prerequisites
- Python 3.10+ recommended
- Ollama installed and running (for local LLM answers)

### 1) Create venv + install dependencies
From repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2) Start the local LLM (Ollama)
Pull the model used by the code:
ollama pull llama3.2:3b
3) Start the FastAPI server
uvicorn src.api.server:app --reload --port 8000
4) Start the Streamlit UI
Open a new terminal (same venv), then:
streamlit run app.py
How to use
Option A: Use the UI (recommended)
Open the Streamlit app in the browser
Upload PDF/TXT files
Click Index / Ingest
Ask questions
Review citations + retrieved sources
Option B: Use the API directly
Health check
curl http://127.0.0.1:8000/health
Trigger indexing (indexes everything in data/raw/)
curl -X POST http://127.0.0.1:8000/ingest
Ask a question
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this document about?","k":4}'
CLI mode (optional)
You can also run via CLI.
Ingest/index
python -m src.main --ingest
Ask a question
python -m src.main --ask "your question here" --k 4
Evaluation
Run evaluation
python -m src.eval.run_eval --eval eval_set.jsonl --k 4
Eval file format (eval_set.jsonl)
One JSON object per line:
{"question":"...", "must_include":["keyword1","keyword2"], "k":4}
The eval runner checks:
whether required keywords appear in the answer
whether cited chunks contain the required keywords (basic grounding proxy)
Configuration
Environment variables (recommended)
Create a .env file in the repo root (do NOT commit it).
Example .env:
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
CHROMA_DIR=data/processed/chroma
Tip: Create a .env.example for public repos with placeholder values.
Project structure
RAG-CITE-EVAL/
├─ app.py                     # Streamlit UI
├─ requirements.txt
├─ eval_set.jsonl             # Evaluation questions (JSONL)
├─ LICENSE
├─ .gitignore
├─ .env                       # local only (do not commit)
├─ data/
│  ├─ raw/                    # Put PDFs/TXT here
│  └─ processed/
│     └─ chroma/              # Persistent Chroma vector DB
└─ src/
   ├─ api/
   │  ├─ __init__.py
   │  └─ server.py            # FastAPI backend (upload/ingest/ask)
   ├─ rag/
   │  ├─ __init__.py
   │  ├─ ingest.py            # PDF/TXT loading + chunking
   │  ├─ index.py             # Chroma indexing + embedding
   │  └─ qa.py                # Retrieval + LLM answer with citations
   ├─ eval/
   │  └─ run_eval.py          # Evaluation runner
   └─ main.py                 # CLI entry point
API endpoints (summary)
GET /health — server health check
POST /upload — upload a file into data/raw/
GET /files — list files in data/raw/
POST /ingest — ingest + index documents from data/raw/
POST /ask — ask a question and return cited answer + sources
Troubleshooting
1) “Ollama not running” / connection refused
Check:
curl http://localhost:11434
If it fails, start Ollama and retry.
2) First run is slow
Normal. The embedding model downloads on first run and indexing takes time depending on PDF size and chunk count.
3) Retrieval returns nothing
Confirm files exist in data/raw/
Re-ingest:
curl -X POST http://127.0.0.1:8000/ingest
4) Mac / laptop becomes slow
Try smaller PDFs
Reduce k (e.g., 3–4)
Index fewer chunks (add a chunk cap in ingest)
Roadmap (nice upgrades)
Add hosted LLM option (for cloud demo)
Add Docker + docker-compose for one-command run
Improve eval metrics: citation precision/recall, faithfulness scoring
Add sample docs and a demo GIF
License
MIT — see LICENSE.
Author
Revanth (portfolio project)