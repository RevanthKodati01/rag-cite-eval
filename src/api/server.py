from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from fastapi import UploadFile, File
import os
import shutil

from src.rag.ingest import ingest_folder
from src.rag.index import index_chunks
from src.rag.qa import retrieve, answer_with_citations

app = FastAPI(title="rag-cite-eval")

class AskRequest(BaseModel):
    question: str
    k: int = 5

class AskResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ingest")
def ingest():
    chunks = ingest_folder("data/raw")
    n = index_chunks(chunks)
    return {"indexed_chunks": n}

@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    hits = retrieve(req.question, k=req.k)

    # Return sources with metadata + snippet (useful for UI)
    sources = []
    for i, h in enumerate(hits, start=1):
        m = h["metadata"]
        sources.append({
            "rank": i,
            "source": m.get("source"),
            "page": m.get("page"),
            "chunk": m.get("chunk"),
            "snippet": (h["text"][:450].replace("\n", " ") + "...") if h.get("text") else "",
        })

    answer = answer_with_citations(req.question, hits)
    return {"answer": answer, "sources": sources}
@app.post("/upload")
def upload(file: UploadFile = File(...)):
    os.makedirs("data/raw", exist_ok=True)
    save_path = os.path.join("data/raw", file.filename)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"saved_as": file.filename}
@app.get("/files")
def list_files():
    os.makedirs("data/raw", exist_ok=True)

    files = []
    for name in os.listdir("data/raw"):
        # hide dotfiles like .gitkeep, .DS_Store
        if name.startswith("."):
            continue

        path = os.path.join("data/raw", name)
        # only include real files
        if os.path.isfile(path):
            files.append(name)

    return {"files": sorted(files)}

