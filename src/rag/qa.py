from typing import List, Dict
import requests

from .index import get_client, get_collection

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"  # small + fast

def retrieve(query: str, k: int = 4, persist_dir: str = "data/processed/chroma") -> List[Dict]:
    client = get_client(persist_dir)
    col = get_collection(client)
    res = col.query(query_texts=[query], n_results=k)

    hits = []
    for i in range(len(res["documents"][0])):
        hits.append({
            "text": res["documents"][0][i],
            "metadata": res["metadatas"][0][i],
            "id": res["ids"][0][i],
        })
    return hits

def format_context(hits: List[Dict]) -> str:
    blocks = []
    for idx, h in enumerate(hits, start=1):
        meta = h["metadata"]
        src = meta.get("source")
        page = meta.get("page")
        label = f"[{idx}] {src}" + (f" p.{page}" if isinstance(page, int) and page > 0 else "")
        blocks.append(f"{label}\n{h['text']}")
    return "\n\n---\n\n".join(blocks)

def answer_with_citations(question: str, hits: List[Dict]) -> str:
    context = format_context(hits)

    prompt = f"""You are a helpful assistant.
Answer ONLY using the provided sources.
Every factual sentence must include citations like [1] or [1][2].
If sources do not contain the answer, say you don't know.

Question: {question}

Sources:
{context}

Write:
1) Answer (with citations)
2) Sources used (just the bracket numbers)
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2}
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["response"].strip()
