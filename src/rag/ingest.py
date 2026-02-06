import os
import fitz  # pymupdf
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Chunk:
    text: str
    metadata: Dict

def load_pdf(path: str) -> List[Dict]:
    try:
        doc = fitz.open(path)
    except Exception as e:
        print(f"[WARN] Skipping unreadable PDF: {path} ({e})")
        return []

    pages = []
    for i in range(len(doc)):
        txt = doc[i].get_text("text").strip()
        if txt:
            pages.append({"text": txt, "page": i + 1})
    return pages



def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150):
    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])

        if end == n:
            break  # 🔥 THIS prevents infinite loop

        start = end - overlap
        if start < 0:
            start = 0

    return [c.strip() for c in chunks if c.strip()]

def ingest_folder(folder: str, max_chunks: int = 300) -> List[Chunk]:
    all_chunks: List[Chunk] = []
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isdir(fpath):
            continue

        if fname.lower().endswith(".pdf"):
            pages = load_pdf(fpath)
            for p in pages:
                for idx, ch in enumerate(chunk_text(p["text"])):
                    all_chunks.append(
                        Chunk(
                            text=ch,
                            metadata={"source": fname, "page": p["page"], "chunk": idx}
                        )
                    )

        elif fname.lower().endswith(".txt"):
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()
            for idx, ch in enumerate(chunk_text(text)):
                all_chunks.append(
                    Chunk(
                        text=ch,
                        metadata={"source": fname, "page": 0, "chunk": idx}
                        #metadata={"source": fname, "page": None, "chunk": idx}
                    )
                )
                if len(all_chunks) >= max_chunks:
                    return all_chunks       
    return all_chunks
