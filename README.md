# RAG-CITE-EVAL 🔎📄✅
A production-style **Retrieval-Augmented Generation (RAG)** portfolio project that answers questions over your documents **with citations** and includes a simple **evaluation harness** to sanity-check grounding.

**Tech Stack:** Python • Streamlit • FastAPI • ChromaDB • Sentence-Transformers • PyMuPDF • Ollama (local LLM)

> **Goal:** Anyone can clone this repo, run it locally, upload PDFs/TXT, index them, and ask questions with **source-backed** answers.

---

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quickstart (Local)](#quickstart-local)
- [Using the App](#using-the-app)
- [API Reference](#api-reference)
- [Evaluation](#evaluation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Performance Notes](#performance-notes)
- [Roadmap](#roadmap)
- [Security & Secrets](#security--secrets)
- [License](#license)
- [Author](#author)

---

## Overview
**RAG-CITE-EVAL** is a document Q&A system with **citation-first** generation.

### How it works (end-to-end)
1. **Ingest** documents from `data/raw/` (PDF / TXT)
2. **Chunk** text into overlapping segments (better retrieval)
3. **Embed + Index** chunks into a persistent vector database (**ChromaDB**) stored at `data/processed/chroma/`
4. For each user question:
   - **Retrieve** top-K relevant chunks from ChromaDB
   - Send retrieved passages to an LLM (**Ollama**) with strict instructions to respond **with citations** like `[1] [2]`
5. Optional: Run an **evaluation set** (`eval_set.jsonl`) to check if answers contain required keywords and whether citations support them.

---

## Key Features
- ✅ **Cited Answers**: Every factual sentence is encouraged/forced to include citations like `[1]`
- ✅ **Upload + Index Workflow** (Streamlit UI)
- ✅ **FastAPI backend** that exposes `/upload`, `/ingest`, `/ask`
- ✅ **Persistent ChromaDB storage** (keeps your index across runs)
- ✅ **Evaluation runner** (JSONL-based) to sanity-check grounding

---

## Architecture
**UI → API → Vector DB + LLM**

- **Streamlit (`app.py`)**: User interface for uploading files, indexing, asking questions
- **FastAPI (`src/api/server.py`)**: Handles ingest, indexing, retrieval, answering
- **RAG modules (`src/rag/`)**:
  - `ingest.py` → load PDFs/TXT + chunking
  - `index.py` → embedding + ChromaDB indexing
  - `qa.py` → retrieval + LLM prompting + citation formatting
- **Eval (`src/eval/run_eval.py`)**: Runs a small suite over `eval_set.jsonl`

---

## Project Structure
```text
RAG-CITE-EVAL/
├─ app.py                     # Streamlit UI
├─ requirements.txt            # Python dependencies
├─ eval_set.jsonl              # Evaluation questions (JSONL)
├─ LICENSE
├─ .gitignore
├─ .env                        # local only (DO NOT commit)
├─ data/
│  ├─ raw/                     # Put PDFs/TXT here
│  └─ processed/
│     └─ chroma/               # Persistent Chroma vector DB
└─ src/
   ├─ api/
   │  ├─ __init__.py
   │  └─ server.py             # FastAPI backend (upload/ingest/ask)
   ├─ rag/
   │  ├─ __init__.py
   │  ├─ ingest.py             # PDF/TXT loading + chunking
   │  ├─ index.py              # Chroma indexing + embeddings
   │  └─ qa.py                 # Retrieval + LLM answering w/ citations
   ├─ eval/
   │  └─ run_eval.py           # Evaluation runner
   └─ main.py                  # CLI entry point
```

---

## Quickstart (Local)

### 0) Prerequisites
- **Python 3.10+** recommended
- **Ollama** installed and running (local LLM)
- macOS/Linux terminal commands below (Windows users can adapt)

### 1) Create a virtual environment + install dependencies
From the repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start the local LLM (Ollama)
Pull the model used by the code:

```bash
ollama pull llama3.2:3b
```

Verify Ollama is responding:

```bash
curl http://localhost:11434
```

### 3) Start the FastAPI server
```bash
uvicorn src.api.server:app --reload --port 8000
```

Check health:

```bash
curl http://127.0.0.1:8000/health
```

### 4) Start the Streamlit UI
Open a new terminal (same venv), then:

```bash
streamlit run app.py
```

---

## Using the App

### A) Streamlit workflow (recommended)
1. Open Streamlit in your browser
2. Upload PDF/TXT files
3. Click **Index / Ingest** (this chunks + embeds + stores in ChromaDB)
4. Ask a question
5. Review:
   - Answer with citations `[1] [2]`
   - Retrieved sources/snippets

### B) API workflow (curl)
#### 1) Upload a document
```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "file=@data/raw/your_doc.pdf"
```

#### 2) Ingest + index everything in `data/raw/`
```bash
curl -X POST "http://127.0.0.1:8000/ingest"
```

#### 3) Ask a question
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Summarize the document in 5 bullets.","k":4}'
```

---

## API Reference
### `GET /health`
Returns server status.

### `POST /upload`
Uploads a file to `data/raw/`.

- Form field: `file` (PDF or TXT)

### `GET /files`
Lists files currently in `data/raw/`.

### `POST /ingest`
Reads all documents in `data/raw/`, chunks them, embeds them, and indexes into ChromaDB.

### `POST /ask`
Request body:
```json
{
  "question": "Your question here",
  "k": 4
}
```

Response includes:
- `answer`: model response with citations
- `sources`: ranked list of source chunks (file/page/chunk/snippet)

---

## Evaluation
This repo includes a simple eval runner that checks whether:
1. Required keywords appear in the answer (`must_include`)
2. The cited chunks contain those keywords (basic grounding proxy)

### Run eval
```bash
python -m src.eval.run_eval --eval eval_set.jsonl --k 4
```

### Eval format (`eval_set.jsonl`)
One JSON object per line:
```json
{"question":"...", "must_include":["keyword1","keyword2"], "k":4}
```

---

## Configuration

### Environment variables
Create a `.env` in the repo root (do NOT commit). Example:

```bash
# LLM (Ollama)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Chroma
CHROMA_DIR=data/processed/chroma
```

**Recommended:** add a `.env.example` for public repos with placeholders.

---

## Troubleshooting

### 1) Uvicorn error: `python-multipart` missing
If you see errors around `python-multipart`, install it:
```bash
pip install python-multipart
```

### 2) “Ollama not running” / connection refused
Check:
```bash
curl http://localhost:11434
```
If it fails, open Ollama and retry.

### 3) Index exists but retrieval returns nothing
- Confirm your files are in `data/raw/`
- Re-ingest:
```bash
curl -X POST http://127.0.0.1:8000/ingest
```

### 4) First run is slow
Normal:
- The embedding model downloads on first run
- Indexing time depends on PDF size and number of chunks

---

## Performance Notes
- Large PDFs can create many chunks → indexing and querying may be slow on laptops.
- Ways to improve:
  - Reduce chunk count (lower `max_chunks` in ingestion)
  - Use smaller PDFs for demos
  - Reduce `k` from 6 → 4 or 3
  - Use a smaller/faster embedding model

---

## Roadmap
- Docker + docker-compose for one-command run
- Hosted-LLM toggle (cloud demo option)
- Better eval metrics: citation precision/recall, faithfulness scoring
- Add sample documents + demo GIF for GitHub/LinkedIn

---

## Security & Secrets
- ✅ Do **NOT** commit `.env` files or API keys.
- If a key was ever uploaded anywhere public:
  - **Rotate/revoke it immediately**
  - Remove it from git history if needed

---

## License
MIT — see `LICENSE`.

---

## Author
**Revanth** — portfolio project (RAG with citations + evaluation harness).
