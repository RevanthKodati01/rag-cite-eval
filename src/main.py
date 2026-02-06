import argparse
from src.rag.ingest import ingest_folder
from src.rag.index import index_chunks
from src.rag.qa import retrieve, answer_with_citations

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ingest", action="store_true", help="Ingest documents from data/raw into Chroma")
    p.add_argument("--ask", type=str, help="Ask a question")
    p.add_argument("--k", type=int, default=4, help="Top-k chunks to retrieve")
    args = p.parse_args()

    if args.ingest:
        chunks = ingest_folder("data/raw")
        n = index_chunks(chunks)
        print(f"Indexed {n} chunks.")

    if args.ask:
        hits = retrieve(args.ask, k=args.k)
        print("\nTop sources:")
        
        for i, h in enumerate(hits, start=1):
            m = h["metadata"]
            print(f"[{i}] {m.get('source')} p.{m.get('page')} chunk {m.get('chunk')}")
        for i, h in enumerate(hits, start=1):
            m = h["metadata"]
            page = m.get("page")
            page_str = f"p.{page}" if isinstance(page, int) and page > 0 else "txt"
            snippet = h["text"][:300].replace("\n", " ")
            print(f"[{i}] {m.get('source')} ({page_str}) — {snippet}...")


        print("\n---\n")
        out = answer_with_citations(args.ask, hits)
        print(out)

if __name__ == "__main__":
    main()
