"""Retrieval over the PSI knowledge base (data/gold/rag/chunks.jsonl).

Default: BM25 (rank_bm25), index cached in memory. If embeddings are available and ./chroma_db was ingested,
hybrid = Chroma vector search + BM25 merged with reciprocal rank fusion (RRF). Optional filter by investigation.
The tokenizer keeps hyphenated acronyms (BASS-II, SAME-R, CFI-G) AND their parts, so exact acronyms match well.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from rank_bm25 import BM25Okapi

from .config import ROOT, get_embeddings

CHUNKS = ROOT / "data" / "gold" / "rag" / "chunks.jsonl"
STOP = set("the a an of in on at to for and or is are was were be been with by from as that this it its what which how why do does "
           "did can could would should will about into than then there their they them i we you me my our your any some".split())
SYN = {
    "acrylic": ["pmma"], "plexiglass": ["pmma"], "pmma": ["acrylic"], "nomex": ["aramid"], "aramid": ["nomex"],
    "sibal": ["cotton", "fiberglass"], "moon": ["lunar"], "lunar": ["moon"], "mars": ["martian"], "martian": ["mars"],
    "smoke": ["particle", "aerosol"], "detector": ["detection", "smoke"], "detectors": ["detection", "smoke", "detector"],
    "extinguish": ["suppression", "extinction"], "suppression": ["suppressant", "extinguishment"], "earth": ["terrestrial", "benefits"],
    "oxygen": ["o2"], "o2": ["oxygen"], "flammability": ["flammable", "burning"], "burn": ["burning", "flame", "combustion"],
    "fire": ["flame", "combustion"], "model": ["modeling", "computational", "simulation"], "dust": ["daft", "aerosol"],
}
_WORD = re.compile(r"[a-z0-9][a-z0-9]*(?:[-.][a-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    """Lower-case words; hyphenated terms kept whole and also split ('bass-ii' -> 'bass-ii', 'bass', 'ii')."""
    out = []
    for w in _WORD.findall((text or "").lower()):
        if w in STOP:
            continue
        out.append(w)
        if "-" in w:
            out += [p for p in w.split("-") if len(p) > 1 and p not in STOP]
    return out


@lru_cache(maxsize=1)
def chunks() -> list[dict]:
    with open(CHUNKS, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


@lru_cache(maxsize=1)
def _bm25() -> BM25Okapi:
    return BM25Okapi([tokenize(c["text"] + " " + (c.get("title") or "")) for c in chunks()])


def _expand(q: list[str]) -> list[str]:
    return q + [s for w in q for s in SYN.get(w, [])]


def _match(c: dict, investigation: str | None, content_type: str | None) -> bool:
    if investigation:
        inv = investigation.upper()
        if inv != (c.get("investigation_id") or "").upper() and inv not in [r.upper() for r in c.get("related_investigations") or []]:
            return False
    return not content_type or c.get("content_type") == content_type


def bm25_search(query: str, k: int = 6, investigation: str | None = None, content_type: str | None = None) -> list[dict]:
    q = _expand(tokenize(query))
    if not q:
        return []
    scores = _bm25().get_scores(q)
    ranked = sorted(((s, i) for i, s in enumerate(scores) if s > 0 and _match(chunks()[i], investigation, content_type)), reverse=True)
    return [dict(chunks()[i], score=round(float(s), 3)) for s, i in ranked[:k]]


def _vector_search(query: str, k: int) -> list[dict] | None:
    emb = get_embeddings()
    if emb is None or not (ROOT / "chroma_db").is_dir():
        return None
    try:
        from langchain_chroma import Chroma
        db = Chroma(collection_name="astrofire", persist_directory=str(ROOT / "chroma_db"), embedding_function=emb)
        by_id = {c["chunk_id"]: c for c in chunks()}
        return [by_id[d.metadata["chunk_id"]] for d in db.similarity_search(query, k=k) if d.metadata.get("chunk_id") in by_id]
    except Exception:
        return None


def search(query: str, k: int = 6, investigation: str | None = None, content_type: str | None = None) -> list[dict]:
    """BM25, or BM25 + vectors fused with RRF when embeddings were ingested."""
    lexical = bm25_search(query, k * 3, investigation, content_type)
    vec = _vector_search(query, k * 3)
    if not vec:
        return lexical[:k]
    vec = [c for c in vec if _match(c, investigation, content_type)]
    fused: dict[str, float] = {}
    for lst in (lexical, vec):
        for rank, c in enumerate(lst):
            fused[c["chunk_id"]] = fused.get(c["chunk_id"], 0) + 1 / (60 + rank)
    by_id = {c["chunk_id"]: c for c in lexical + vec}
    return [dict(by_id[cid], score=round(s, 4)) for cid, s in sorted(fused.items(), key=lambda kv: -kv[1])[:k]]


def mode() -> str:
    return "hybrid" if _vector_search("test", 1) else "bm25"
