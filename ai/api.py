"""FastAPI router for the AI layer.

  POST /api/ask            analyst contract {question, habitat?, history?} -> answer, findings[], interpretation[], limits[],
                           followups[], tools_used[], mode, model (+ intent, evidence, sources ...)
  GET  /api/ask/status     ai_enabled, provider, model, retrieval mode (never keys)
  POST /ai/chat            same as /api/ask (chatbot UI)
  POST /ai/ask             {question, investigation?} -> {answer, sources[]}
  POST /ai/scenario        {environment, o2, pressure, material?, fuel_type?} -> {verdict, coverage, reasons[], evidence[] ...}
  POST /ai/compare         {ids: [2-3]} -> {table, narrative, sources}
  POST /ai/gaps            {scenario?} -> {gaps[], covered[], cells[], narrative}
  GET  /ai/summary/{id}    -> {objective, materials, conditions, outcome_summary, caveats, sources}
  GET  /ai/health
Every response carries request_id + latency_ms. Errors are clean JSON, never a stack trace.
Optional X-API-Key check for /ai/* when AI_API_KEY is set. Per-client rate limit. In-memory LRU cache for the demo.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from collections import OrderedDict, defaultdict, deque

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from . import features as F
from . import retrieval
from .chat import analyze
from .config import llm_status, setting
from .schemas import AskIn, CompareIn, GapsIn, ScenarioIn, SimpleAskIn
from .tools import ToolError

log = logging.getLogger("astrofire.ai")
router = APIRouter()
RATE, WINDOW = int(setting("AI_RATE_LIMIT", "20") or 20), 60.0   # requests per client per minute on AI endpoints
_hits: dict[str, deque] = defaultdict(deque)
_cache: OrderedDict = OrderedDict()
CACHE_SIZE = 256


def _client(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def guard(request: Request, x_api_key: str | None = Header(None)):
    """Optional API key (only if AI_API_KEY is set) + sliding-window rate limit."""
    want = setting("AI_API_KEY")
    if want and x_api_key != want and request.url.path.startswith("/ai/"):
        raise HTTPException(401, "Missing or wrong X-API-Key.")
    q, now = _hits[_client(request)], time.time()
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= RATE:
        raise HTTPException(429, f"Too many AI requests: limit {RATE} per minute. Try again shortly.")
    q.append(now)


def _key(name: str, payload) -> str:
    return name + ":" + hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).lower().encode()).hexdigest()


def _run(name: str, payload, fn):
    """Cache + timing + clean errors around a feature call."""
    t0, rid = time.time(), uuid.uuid4().hex[:12]
    k = _key(name, payload)
    if k in _cache:
        _cache.move_to_end(k)
        out = dict(_cache[k], cached=True)
    else:
        try:
            out = F.public(fn())
        except ToolError as e:
            raise HTTPException(422, str(e))
        except HTTPException:
            raise
        except Exception as e:  # never leak a stack trace
            log.exception("AI feature %s failed", name)
            raise HTTPException(500, f"The AI feature '{name}' failed ({type(e).__name__}). The data endpoints still work.")
        _cache[k] = out
        if len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
    return {**out, "request_id": rid, "latency_ms": int((time.time() - t0) * 1000)}


@router.get("/api/ask/status")
def ask_status():
    return {**llm_status(), "retrieval": retrieval.mode(), "knowledge_base_chunks": len(retrieval.chunks())}


@router.get("/ai/health")
def health():
    return {"ok": True, **ask_status()}


@router.post("/api/ask", dependencies=[Depends(guard)])
def api_ask(body: AskIn):
    hist = [t.model_dump() for t in body.history]
    return _run("analyst", body.model_dump(), lambda: analyze(body.question, body.habitat, hist))


@router.post("/ai/chat", dependencies=[Depends(guard)])
def ai_chat(body: AskIn):
    return api_ask(body)


@router.post("/ai/ask", dependencies=[Depends(guard)])
def ai_ask(body: SimpleAskIn):
    return _run("ask", body.model_dump(), lambda: F.ask(body.question, body.investigation))


@router.post("/ai/scenario", dependencies=[Depends(guard)])
def ai_scenario(body: ScenarioIn):
    return _run("scenario", body.model_dump(), lambda: F.scenario(**body.model_dump()))


@router.post("/ai/compare", dependencies=[Depends(guard)])
def ai_compare(body: CompareIn):
    return _run("compare", body.model_dump(), lambda: F.compare(body.ids))


@router.post("/ai/gaps", dependencies=[Depends(guard)])
def ai_gaps(body: GapsIn | None = None):
    sc = body.scenario.model_dump() if body and body.scenario else None
    return _run("gaps", sc, lambda: F.gaps(sc))


@router.get("/ai/summary/{investigation_id}", dependencies=[Depends(guard)])
def ai_summary(investigation_id: str):
    if len(investigation_id) > 40:
        raise HTTPException(422, "Investigation id too long.")
    return _run("summary", investigation_id.upper(), lambda: F.experiment_summary(investigation_id))


def warmup() -> dict:
    """Load the BM25 index and precompute the 'what burned' summaries. No network calls for embeddings."""
    t0 = time.time()
    n = len(retrieval.chunks())
    retrieval.bm25_search("warm up", 1)
    s = F.warm_summaries()
    return {"chunks": n, "summaries": s, "seconds": round(time.time() - t0, 2)}
