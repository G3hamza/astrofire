"""Settings, LLM and (optional) embeddings. Nothing here touches the network at import time.

LLM: provider-agnostic via LangChain init_chat_model (groq | anthropic | openai | google_genai), temperature 0 where the
model accepts it, retry with backoff, optional automatic fallback provider. No key -> get_llm() returns None and every
feature answers in template mode.
Embeddings: offline-first. Used only if ./models/all-MiniLM-L6-v2 exists (or EMBEDDINGS_BACKEND says so); never downloaded.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger("astrofire.ai")

try:  # .env is optional; values already in the environment win
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
except ImportError:  # pragma: no cover
    pass

KEY_VARS = {"groq": "GROQ_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY", "google_genai": "GOOGLE_API_KEY"}
# Models that reject a temperature parameter (current Claude models): omit it for them.
NO_TEMPERATURE_PREFIXES = ("claude-",)
LOCAL_EMBED_DIR = ROOT / "models" / "all-MiniLM-L6-v2"

_override_llm = None  # tests inject a fake LLM here (set_llm)


def setting(name: str, default: str = "") -> str:
    v = os.getenv(name, default)
    return (v or default).split("#")[0].strip()


def provider() -> str:
    return setting("LLM_PROVIDER", "groq")


def model_name() -> str:
    return setting("LLM_MODEL", "openai/gpt-oss-120b")


def has_key(prov: str | None = None) -> bool:
    return bool(setting(KEY_VARS.get(prov or provider(), "")))


def _build(prov: str, model: str, max_retries: int = 2):
    from langchain.chat_models import init_chat_model
    kwargs = {"max_retries": max_retries, "timeout": 30}
    if not model.startswith(NO_TEMPERATURE_PREFIXES):
        kwargs["temperature"] = 0
    if prov == "groq" and model.startswith(("openai/gpt-oss", "qwen/")):  # reasoning models: keep answers fast
        kwargs["reasoning_effort"] = setting("LLM_REASONING_EFFORT", "low")
    if prov == "anthropic":
        kwargs["max_tokens"] = 4000  # room for adaptive thinking + the answer (Claude Haiku 5.5 thinks by default)
    return init_chat_model(model, model_provider=prov, **kwargs)


def fallbacks() -> list[tuple[str, str]]:
    """Ordered fallback chain with a configured key. LLM_FALLBACKS="groq:qwen/qwen3.8-27b,anthropic:claude-haiku-5-5"
    (provider:model, comma-separated); the single LLM_FALLBACK_PROVIDER / LLM_FALLBACK_MODEL pair is appended if set."""
    out = []
    for item in setting("LLM_FALLBACKS").split(","):
        if ":" in item:
            p, m = item.strip().split(":", 1)
            out.append((p.strip(), m.strip()))
    p, m = setting("LLM_FALLBACK_PROVIDER"), setting("LLM_FALLBACK_MODEL")
    if p and m:
        out.append((p, m))
    seen, chain = set(), []
    for p, m in out:
        if (p, m) not in seen and (p, m) != (provider(), model_name()) and has_key(p):
            seen.add((p, m)); chain.append((p, m))
    return chain


def fallback() -> tuple[str, str] | None:
    fb = fallbacks()
    return fb[0] if fb else None


def set_llm(llm) -> None:
    """Tests: inject a fake chat model (or None to force template mode). Pass 'reset' to go back to .env settings."""
    global _override_llm
    _override_llm = llm
    get_llm.cache_clear()


class ChainExhausted(RuntimeError):
    """Every model in the chain failed; .events says why each one was skipped."""

    def __init__(self, events: list[str]):
        super().__init__("all models failed: " + "; ".join(events))
        self.events = events


class ModelChain:
    """Explicit failover: try each model in order; a rate limit, outage or error moves to the next one in about a second.
    The returned message carries response_metadata['served_by'] and ['skipped'] (one line per model that failed)."""

    def __init__(self, links: list[tuple[str, object]]):
        self.links = links

    def invoke(self, messages, **kw):
        skipped = []
        for name, model in self.links:
            try:
                msg = model.invoke(messages, **kw)
            except Exception as e:  # rate limit, no credits, timeout, provider down ...
                skipped.append(f"{name}:{type(e).__name__}")
                log.warning("StarryNight AI: %s failed (%s) - trying the next model.", name, type(e).__name__)
                continue
            meta = dict(getattr(msg, "response_metadata", None) or {})
            meta.setdefault("model_name", name)
            meta["served_by"], meta["skipped"] = name, skipped
            try:
                msg.response_metadata = meta
            except Exception:
                pass
            return msg
        raise ChainExhausted(skipped)


@lru_cache(maxsize=1)
def get_llm():
    """The model chain (primary + fallbacks); None when no key is configured (template mode)."""
    if _override_llm is not None:
        return None if _override_llm == "none" else _override_llm
    prov, model = provider(), model_name()
    order = ([(prov, model)] if has_key(prov) else []) + fallbacks()
    if not order:
        log.warning("StarryNight AI: %s is not set - answers use deterministic templates (no LLM).", KEY_VARS.get(prov, "API key"))
        return None
    links = []
    for i, (p, m) in enumerate(order):
        try:  # every link but the last fails fast (no client retries) so failover takes about a second
            links.append((m, _build(p, m, max_retries=0 if i < len(order) - 1 else 1)))
        except Exception as e:  # missing provider package, bad model id ...
            log.warning("StarryNight AI: could not start %s/%s (%s) - skipped.", p, m, type(e).__name__)
    return ModelChain(links) if links else None


def llm_status() -> dict:
    """Safe to return to the browser: never includes keys."""
    on = get_llm() is not None
    fake = _override_llm not in (None, "none")
    return {"ai_enabled": on, "provider": ("fake" if fake else provider()) if on else None,
            "model": ("fake" if fake else model_name()) if on else None,
            "fallback": setting("LLM_FALLBACK_MODEL") or None, "fallback_ready": bool(fallback()),
            "fallback_chain": [m for _, m in fallbacks()],
            "key_configured": has_key(), "embeddings": embeddings_backend()}


def embeddings_backend() -> str:
    b = setting("EMBEDDINGS_BACKEND").lower()
    if b:
        return b
    return "local_folder" if LOCAL_EMBED_DIR.is_dir() else "none"


@lru_cache(maxsize=1)
def get_embeddings():
    """Offline-first embeddings or None. Never downloads automatically; one warning when unavailable."""
    b = embeddings_backend()
    if b == "none":
        log.warning("StarryNight AI: embeddings unavailable - BM25-only retrieval (nothing to ingest).")
        return None
    try:
        if b == "local_folder":
            if not LOCAL_EMBED_DIR.is_dir():
                raise FileNotFoundError(LOCAL_EMBED_DIR)
            from langchain_huggingface import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(model_name=str(LOCAL_EMBED_DIR), model_kwargs={"local_files_only": True})
        if b == "huggingface":
            from langchain_huggingface import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        if b == "fastembed":
            from langchain_community.embeddings import FastEmbedEmbeddings
            return FastEmbedEmbeddings()
    except Exception as e:
        log.warning("StarryNight AI: embeddings backend '%s' unavailable (%s) - BM25-only retrieval.", b, type(e).__name__)
    return None
