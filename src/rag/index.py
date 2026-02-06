import chromadb
from chromadb.utils import embedding_functions
from typing import List
from .ingest import Chunk

def get_client(persist_dir: str = "data/processed/chroma"):
    return chromadb.PersistentClient(path=persist_dir)

def get_collection(client, name: str = "rag_cite_eval"):
    emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="paraphrase-MiniLM-L3-v2"
    )
    return client.get_or_create_collection(name=name, embedding_function=emb_fn)

def index_chunks(chunks: List[Chunk], persist_dir: str = "data/processed/chroma") -> int:
    if not chunks:
        print("[WARN] No chunks to index.")
        return 0

    client = get_client(persist_dir)
    col = get_collection(client)

    BATCH = 64
    total = 0

    for start in range(0, len(chunks), BATCH):
        batch = chunks[start:start+BATCH]
        ids, docs, metas = [], [], []
        for i, c in enumerate(batch, start=start):
            ids.append(f'{c.metadata["source"]}:{c.metadata["page"]}:{c.metadata["chunk"]}:{i}')
            docs.append(c.text)
            metas.append(c.metadata)
        for m in metas:
            for k, v in m.items():
                if v is None:
                    raise ValueError(f"Metadata contains None -> key={k}, metadata={m}")

        col.add(ids=ids, documents=docs, metadatas=metas)
        total += len(ids)

    return total

