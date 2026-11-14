"""Entity extraction for the chat router. Reuses backend/scenario_parse.py, but keeps ONLY what the user actually said:
no default material (unknown stays unknown), no default oxygen/pressure. Adds spacecraft / rover habitats.
"""
from __future__ import annotations

import re

from backend.scenario_parse import parse

HAB_WORDS = [(r"\brover\b", "rover"), (r"\bmars\b|\bmartian\b", "mars"), (r"\bmoon\b|\blunar\b|artemis", "moon"),
             (r"\bspacecraft\b|\bcapsule\b|in transit", "spacecraft"), (r"exploration atmosphere|8\.2 ?psi", "exploration"),
             (r"\biss\b|space station", "iss")]
MAT_WORD = re.compile(r"\b(pmma|acrylic|nomex|aramid|sibal|cotton|ultem|silicone|kapton|teflon|lampwick|pyrell|wax|methanol|heptane)\b", re.I)


def extract(text: str) -> dict:
    p = parse(text or "")
    got = {u["field"]: u["value"] for u in p["understood"]}
    hab = next((k for pat, k in HAB_WORDS if re.search(pat, text or "", re.I)), None)
    mw = MAT_WORD.search(text or "")
    return {"habitat": hab, "material": got.get("material") if "material" in got else None,
            "material_word": mw.group(1) if mw else None, "o2": got.get("o2_pct"), "pressure": got.get("pressure_kpa"),
            "gravity": got.get("gravity_g"), "warnings": p["warnings"]}
