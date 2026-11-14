"""Load data/gold/rag/chunks.jsonl into Chroma (optional hybrid retrieval).

    python -m ai.ingest            # idempotent: skips if already ingested with the same embeddings backend
    python -m ai.ingest --rebuild

Only runs when embeddings are available (see ai/config.py). Otherwise it says BM25-only mode is active: nothing to ingest.
Chroma metadata cannot hold lists or None: related_investigations -> comma string + boolean inv_<NAME> flags; None dropped.
"""
import json
import shutil
import sys

from .config import ROOT, embeddings_backend, get_embeddings
from .retrieval import chunks

DB = ROOT / "chroma_db"
STAMP = DB / "astrofire_ingest.json"


def metadata(c: dict) -> dict:
    m = {k: v for k, v in c.items() if k not in ("text", "related_investigations") and v is not None and not isinstance(v, (list, dict))}
    inv = c.get("related_investigations") or []
    m["related_investigations"] = ",".join(inv)
    for name in inv:
        m["inv_" + name.replace("-", "_").replace(" ", "_")] = True
    return m


def main() -> int:
    emb = get_embeddings()
    if emb is None:
        print("BM25-only mode is active: embeddings are unavailable on this machine, so there is nothing to ingest.\n"
              "Retrieval works now. To enable hybrid search later, put all-MiniLM-L6-v2 in ./models/ and re-run.")
        return 0
    backend = embeddings_backend()
    if STAMP.exists() and "--rebuild" not in sys.argv:
        s = json.loads(STAMP.read_text())
        if s.get("backend") == backend and s.get("chunks") == len(chunks()):
            print(f"Already ingested ({s['chunks']} chunks, backend {backend}). Use --rebuild to rebuild.")
            return 0
    if DB.exists():
        shutil.rmtree(DB)
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    docs = [Document(page_content=c["text"], metadata=metadata(c)) for c in chunks()]
    Chroma.from_documents(docs, emb, collection_name="astrofire", persist_directory=str(DB), ids=[c["chunk_id"] for c in chunks()])
    STAMP.write_text(json.dumps({"backend": backend, "chunks": len(docs)}))
    print(f"Ingested {len(docs)} chunks into {DB} (backend {backend}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
