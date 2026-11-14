"""Guardrails applied inside every AI feature (not only at the API layer).

(a) no_probability: finds chance/probability/likelihood/confidence wording; legit "30% oxygen" is allowed.
(b) unsupported_numbers: every number in generated text must appear in the evidence (rounding + kPa/psi/atm tolerance).
(c) sanitize: strips instruction-like lines from retrieved text (prompt-injection defense) before it reaches the LLM.
(d) off-topic: is_off_topic() + the exact fallback string OFF_TOPIC.
"""
from __future__ import annotations

import re

OFF_TOPIC = "No data in the NASA papers provided."
INSUFFICIENT = "Insufficient validated experimental evidence."

_PROB = re.compile(
    r"\b\d+(?:\.\d+)?\s*%\s*(?:chance|probability|likelihood|likely|confiden\w*|certain\w*|risk|odds)\b"
    r"|\b(?:probability|probabilities|likelihood|odds)\b"
    r"|\b(?:chance|chances)\s+(?:of|that|to)\b"
    r"|\bconfidence\s*(?:score|level|of|interval|:)|\b\d+(?:\.\d+)?\s*%\s*confident\b|\bconfidence\b",
    re.I)


def no_probability_violations(text: str) -> list[str]:
    return [m.group(0) for m in _PROB.finditer(text or "")]


def strip_probability(text: str) -> str:
    """Remove sentences that state a chance/probability/confidence."""
    parts = re.split(r"(?<=[.!?])\s+", text or "")
    return " ".join(p for p in parts if not _PROB.search(p)).strip()


# A sign counts only at the start or after a space/bracket (so the "-42" in "SAFFIRE-II-42" is not a number).
_NUM = re.compile(r"(?:(?<=^)|(?<=[\s(\[=:;]))[-+]?\d+(?:[.,]\d+)?(?![\w.]*\d)|(?<![\w.\-])\d+(?:[.,]\d+)?(?![\w.]*\d)")
# Identifiers that contain digits but are not measurements: citations, PSI ids, test ids (BASS-II-B21, FLEX-273,
# CFIG-N-21153F1), dates, chemical formulas (C12H26).
_CITE = re.compile(r"\[\d+\]|\bE\d+\b|\b[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*-\d[A-Za-z0-9]*(?:-[A-Za-z0-9]+)*\b"
                   r"|\b[A-Z]+-[IVX]+\b|\b\d{4}-\d{2}-\d{2}\b|\b(?:[A-Z][a-z]?\d+){2,}\b")


def numbers(text: str) -> list[float]:
    t = _CITE.sub(" ", text or "")
    out = []
    for m in _NUM.finditer(t):
        try:
            out.append(float(m.group(0).replace(",", "")))
        except ValueError:
            pass
    return out


def _variants(v: float) -> set[float]:
    """A value and its common unit conversions, so '8.2 psi' matches evidence '56.5 kPa'."""
    return {v, round(v, 1), round(v), v * 6.89476, v / 6.89476, v * 101.325, v / 101.325, v * 100, v / 100}


def unsupported_numbers(text: str, evidence: str, allowed: tuple[float, ...] = ()) -> list[float]:
    """Numbers in text that do not appear (within rounding / unit conversion) in the evidence. Small counts 0-10 are allowed
    only when they appear in evidence too, except list numbering (handled by the caller's prompt format)."""
    ev = set()
    for v in numbers(evidence) + list(allowed):
        ev |= _variants(v)
    bad = []
    for v in numbers(text):
        if any(abs(v - e) <= max(0.06, abs(e) * 0.02) for e in ev):
            continue
        bad.append(v)
    return bad


_INJECT = re.compile(
    r"(ignore|disregard|forget)\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier|system)?\s*(instructions?|prompts?|rules?)"
    r"|you\s+are\s+now\b|act\s+as\b|new\s+instructions?|system\s+prompt|reveal\s+(your|the)\s+(prompt|key|instructions)"
    r"|</?\s*(system|assistant|user|instructions?)\s*>|\bapi[_ -]?key\b|\bsk-[a-z0-9-]{8,}|\bgsk_[a-z0-9]{8,}",
    re.I)


def sanitize(text: str) -> str:
    """Drop instruction-like sentences from untrusted retrieved/NASA text before it is shown to the LLM."""
    parts = re.split(r"(?<=[.!?\n])\s+", text or "")
    return " ".join(p for p in parts if not _INJECT.search(p)).strip()


def looks_like_injection(text: str) -> bool:
    return bool(_INJECT.search(text or ""))


SECRET = re.compile(r"\b(sk-ant-[A-Za-z0-9_-]{10,}|gsk_[A-Za-z0-9]{10,}|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,})")


def redact_secrets(text: str) -> str:
    return SECRET.sub("[redacted]", text or "")


DOMAIN = re.compile(
    r"fire|flam|flame|burn|combust|smoke|soot|oxygen|\bo2\b|o₂|ignit|extingu|suppress|detect|smold|pyroly|material|fabric|"
    r"pmma|acrylic|nomex|aramid|sibal|ultem|cotton|plastic|droplet|fuel|gas|nasa|psi|investigation|experiment|test|data|"
    r"bass|saffire|same|flex|spice|slice|acme|cfi|daft|bre|e-field|habitat|moon|lunar|mars|martian|iss|station|spacecraft|"
    r"rover|cabin|gravity|microgravity|space|astronaut|crew|pressure|kpa|psi\b|atmosphere|safety|gap|rank|compare|summar|"
    r"model|dataset|earth|spinoff|aerosol|dust|particle|apollo|mir|artemis",
    re.I)
OUT_OF_SCOPE = re.compile(r"\brocket\s*(engine|propellant|fuel|motor)s?\b|\bpropellants?\b|\bsolid rocket\b", re.I)


def is_off_topic(question: str, history_has_context: bool = False) -> bool:
    if OUT_OF_SCOPE.search(question or "") and not re.search(r"cabin|material|habitat|crew|smoke", question or "", re.I):
        return True
    return not DOMAIN.search(question or "") and not history_has_context
