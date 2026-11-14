"""Phase 5: data for modeling, equipment implications per fire-safety pillar, Earth applications.

Challenge objectives covered: "extract data that supports predictive modeling", "highlight research that informs the
development of next-generation fire safety controls and equipment", "potential applications of the PSI data on Earth".
Every statement is NASA's own text (investigation.json research impacts / objectives) or the challenge's resources tab,
with its source. StarryNight's own reading is returned separately as `interpretation`, labelled as such.
"""
import csv
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
PSI_SEARCH = "https://psi.nasa.gov/physci/repo/search?q=combustion"

# Downloadable datasets: name -> (path under data/gold, what it is, caveats). Whitelist: nothing else can be downloaded.
DATASETS = {
    "ml_solid_outcomes": ("ml/solid_outcome_features.csv", "ML-ready solid-material space tests with outcomes NASA wrote down (labels).",
                          ["Small: only outcomes written by NASA are labels (inferred ones excluded on purpose).",
                           "Not validated: a logistic baseline scored below 'always predict the majority class'. Exploration only.",
                           "Grouped train/test split column (split, split_group) to limit same-day leakage."]),
    "solid_fire_tests": ("analytics/solid_fire_tests.csv", "All 263 solid-material space fire tests (BASS, BASS-II, Saffire I-III).",
                         ["Pressure is assumed ISS/Cygnus cabin (~101 kPa), not measured (pressure_status).",
                          "outcome_basis: observed (NASA wrote it) / inferred (from notes) / not_recorded. Only observed are ground truth.",
                          "material_identity: named in NASA table vs inferred from the investigation."]),
    "droplet_extinction_tests": ("analytics/droplet_extinction_tests.csv", "FLEX fuel-droplet flames: oxygen, measured pressure, diluent, extinction diameter, burn time.",
                                 ["Liquid fuel droplets, not cabin materials.", "Outcomes written by NASA."]),
    "cool_flame_tests": ("analytics/cool_flame_tests.csv", "CFI cool-flame droplet tests: conditions only.", ["NASA recorded no outcome column."]),
    "gas_flame_tests": ("analytics/gas_flame_tests.csv", "ACME gas flames (CFI-G, Flame Design): oxygen 12-85%, pressure, outcome codes.",
                        ["Gas flames, not cabin materials.", "Flame Design has conditions only."]),
    "smoke_generation_tests": ("analytics/smoke_generation_tests.csv", "SAME / SAME-R smoke from heated (not burning) cabin materials.",
                               ["Smoke from overheating, no flames.", "SAME-R dates lack the year."]),
    "gas_jet_flame_conditions": ("analytics/gas_jet_flame_conditions.csv", "SPICE gas-jet flame conditions (smoke point / soot).", ["Conditions only."]),
    "investigation_profiles": ("analytics/investigation_profiles.csv", "One row per PSI investigation: pillar, tier, hardware, fuel, ranges, sensors.",
                               ["Pillar / tier / hardware are team classifications with a basis (see data/curation/)."]),
}

PILLAR_WORDS = {
    "prevention": r"material|flammab|fire safety|spread|design|screen|standard|ventilat|fire grow|limit",
    "detection": r"detect|sensor|smoke|alarm|particle|instrument",
    "suppression": r"suppress|extingu|inert|CO2|helium|dilut",
}
# StarryNight's reading per pillar. Interpretation, not NASA results: shown separately and labelled.
INTERPRETATION = {
    "prevention": "Material selection for Moon/Mars habitats would need flammability data at higher oxygen and lower pressure than any PSI solid test; "
                  "the PSI results define the cabin-air baseline that new tests (LUCI, FM2) would extend.",
    "detection": "Smoke particle sizes measured in microgravity (SAME, SAME-R) are the reference NASA says future spacecraft detectors will be evaluated against.",
    "suppression": "FLEX measured how CO2 and helium dilution changes when flames go out; that is direct input for choosing extinguishing gases, "
                   "though only for liquid-fuel droplets, not solid materials.",
}
EARTH = re.compile(r"\bon Earth\b|Earth benefit|terrestrial|Earth environments|\bmines?\b|submarine|firefight|practical applications on earth", re.I)


def _sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text or "") if s.strip()]


@lru_cache(maxsize=1)
def _profiles():
    return json.loads((GOLD / "analytics" / "investigation_profiles.json").read_text(encoding="utf-8"))


def datasets():
    """Catalog: real row counts, real columns with how many rows have a value, caveats, download link."""
    out = []
    for name, (rel, what, caveats) in DATASETS.items():
        p = GOLD / rel
        if not p.exists():
            continue
        with open(p, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        cols = list(rows[0].keys()) if rows else []
        out.append({"name": name, "file": f"data/gold/{rel}", "description": what, "rows": len(rows),
                    "columns": [{"name": c, "filled": sum(1 for r in rows if r.get(c) not in ("", None))} for c in cols],
                    "caveats": caveats, "download": f"/api/datasets/{name}.csv", "license": "CC0 (NASA PSI)"})
    ml_readme = GOLD / "ml" / "README.md"
    return {"datasets": out, "ml_readme": ml_readme.read_text(encoding="utf-8") if ml_readme.exists() else None,
            "data_dictionary": "docs/DATA_DICTIONARY.md", "source": PSI_SEARCH}


def dataset_path(name: str):
    item = DATASETS.get(name)
    return (GOLD / item[0]) if item else None


def equipment():
    """Per pillar: the investigations, and NASA's own sentences about detectors / suppression / material design."""
    out = []
    for pillar, words in PILLAR_WORDS.items():
        items = []
        for p in _profiles():
            if pillar not in (p["pillar"], p["pillar_secondary"]):
                continue
            ss = [s for s in _sentences(p.get("research_impacts")) + _sentences(p.get("objective")) if re.search(words, s, re.I)]
            if not ss:
                continue
            items.append({"investigation_id": p["investigation_id"], "acronym": p["acronym"], "relevance_tier": p["relevance_tier"],
                          "nasa_says": ss[:2], "source_field": "research_impacts / objective (NASA PSI investigation.json)",
                          "psi_url": p["psi_url"]})
        order = {"direct": 0, "related": 1, "background": 2}
        items.sort(key=lambda x: (order[x["relevance_tier"]], x["acronym"]))
        out.append({"pillar": pillar, "investigations": items, "interpretation": INTERPRETATION[pillar],
                    "interpretation_label": "StarryNight interpretation (not a NASA result)"})
    return out


def earth():
    """Earth applications: the challenge's resources tab (spinoffs) + NASA's own Earth-benefit sentences per investigation."""
    from pipelines.transformation.rag import CHALLENGE_RESOURCES
    spin = [{"id": cid, "title": title, "url": url, "summary": text}
            for cid, title, url, text in CHALLENGE_RESOURCES if cid.startswith(("CR-spinoff", "CR-water-mist"))]
    psi = []
    for p in _profiles():
        ss = [s for s in _sentences(p.get("research_impacts")) if EARTH.search(s) and not re.search(r"far from Earth", s, re.I)]
        if ss:
            psi.append({"investigation_id": p["investigation_id"], "acronym": p["acronym"], "pillar": p["pillar"],
                        "nasa_says": ss[:2], "psi_url": p["psi_url"]})
    return {"spinoffs": spin, "from_psi_investigations": psi,
            "caveat": "These are connections NASA or the challenge describe. PSI data does not validate any Earth product directly."}
