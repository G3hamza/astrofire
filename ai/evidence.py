"""Evidence registry: every fact shown to the user is an Evidence item with a real source (table row, PSI page or passage).

Items get short ids (E1, E2 ...). The LLM may only cite these ids; citations to unknown ids are dropped.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .guardrails import sanitize


@dataclass
class Evidence:
    id: str
    kind: str                      # record | investigation | passage | ranking | scenario | gap | dataset | resource
    text: str                      # the fact, written from the data (never by the LLM)
    investigation_id: str | None = None
    acronym: str | None = None
    source_file: str | None = None
    source_row: int | None = None
    psi_url: str | None = None
    url: str | None = None
    title: str | None = None
    year: str | None = None
    chunk_id: str | None = None
    level: str = "direct"          # direct (NASA record/text) | related (indirect relevance) | analysis (AstroFire computed)
    extra: dict = field(default_factory=dict)

    def public(self) -> dict:
        d = asdict(self)
        d.pop("extra")
        return {k: v for k, v in d.items() if v is not None}


class Registry:
    def __init__(self):
        self.items: list[Evidence] = []
        self._keys: dict[tuple, str] = {}
        self.tools_used: list[str] = []

    def add(self, kind: str, text: str, **kw) -> Evidence:
        key = (kind, kw.get("source_file"), kw.get("source_row"), kw.get("chunk_id"), kw.get("investigation_id"), text[:80])
        if key in self._keys:
            return self.get(self._keys[key])
        e = Evidence(id=f"E{len(self.items) + 1}", kind=kind, text=sanitize(text), **kw)
        self.items.append(e)
        self._keys[key] = e.id
        return e

    def get(self, eid: str) -> Evidence | None:
        return next((e for e in self.items if e.id == eid), None)

    def used(self, tool: str) -> None:
        if tool not in self.tools_used:
            self.tools_used.append(tool)

    def block(self, ids: list[str] | None = None) -> str:
        """Evidence as numbered lines for the LLM prompt (untrusted data, sanitized), capped to keep prompts small."""
        rows = [e for e in self.items if ids is None or e.id in ids][:24]
        return "\n".join(f"[{e.id}] ({e.kind}{', ' + e.acronym if e.acronym else ''}) {e.text[:520]}" for e in rows)

    def sources(self, ids: list[str] | None = None) -> list[dict]:
        """Teammate 'sources' shape: n, title, year, url, chunk_id, snippet (300 chars)."""
        out = []
        for e in self.items:
            if ids is not None and e.id not in ids:
                continue
            out.append({"n": len(out) + 1, "evidence_id": e.id, "title": e.title or (f"{e.acronym} ({e.investigation_id})" if e.acronym else e.kind),
                        "year": e.year, "url": e.url or e.psi_url, "chunk_id": e.chunk_id, "source_file": e.source_file,
                        "source_row": e.source_row, "snippet": e.text[:300]})
        return out
