"""The five AI features as plain functions (the backend, the chat router, the tests and the eval all call these).

Pattern for every feature: tools gather evidence deterministically -> a deterministic template answer is built ->
if an LLM is configured it rewrites the explanation from that evidence only -> guardrails -> template on any failure.
"""
from __future__ import annotations

import re

from . import guardrails as G
from . import llm as L
from . import tools as T
from .evidence import Registry
from .tables import by_acronym, habitats, profiles

ENV_ALIASES = {"moon": "moon", "lunar": "moon", "mars": "mars", "martian": "mars", "iss": "iss", "station": "iss",
               "spacecraft": "spacecraft", "rover": "rover", "exploration": "exploration"}


def _mode(events: list[str]) -> str:
    return "template" if ("explained_by_analyst" in events or "template_mode" in events or "fell_back_to_template" in events or any(e.startswith("llm_error") for e in events)) else "ai"


def _clean(text: str, reg: Registry) -> str:
    return L.keep_valid_citations(G.strip_probability(G.redact_secrets(text)), {e.id for e in reg.items})


# 1. ASK -------------------------------------------------------------------------------------------------------
def ask(question: str, investigation: str | None = None) -> dict:
    """Cited answer from the PSI knowledge base. {answer, sources[], mode, guardrails}"""
    if G.is_off_topic(question):
        return {"answer": G.OFF_TOPIC, "sources": [], "mode": "template", "guardrails": ["off_topic"]}
    reg = Registry()
    try:
        ids = T.search_passages(reg, question, k=6, investigation=investigation)
    except T.ToolError as e:
        return {"answer": G.OFF_TOPIC, "sources": [], "mode": "template", "guardrails": [str(e)]}
    if not ids:
        return {"answer": G.OFF_TOPIC, "sources": [], "mode": "template", "guardrails": ["no_relevant_passages"]}
    text, ev = L.write("ask", question, reg.block(ids))
    if text is None:  # extractive template: the top passages, each cited
        text = " ".join(f"{reg.get(i).text[:280].rstrip()} [{i}]" for i in ids[:3])
    text = _clean(text, reg)
    if G.OFF_TOPIC in text:
        return {"answer": G.OFF_TOPIC, "sources": [], "mode": _mode(ev), "guardrails": ev}
    used = L.cited_ids(text) or ids[:3]
    return {"answer": text, "sources": reg.sources(used), "mode": _mode(ev), "guardrails": ev}


# 2. SCENARIO EXPLAINER ----------------------------------------------------------------------------------------
def _coverage(r: dict) -> str:
    if r["blockers"]:
        return "Gap"
    return "Directly tested" if r["evidence_distance"] < 1.0 and any(e["same_material"] for e in r["evidence"]) else "Closest evidence"


def scenario(environment: str = "iss", o2: float | None = None, pressure: float | None = None, material: str | None = None,
             fuel_type: str | None = None, gravity_g: float | None = None, flow_cm_s: float = 5.0) -> dict:
    """Verdict from the existing engine (contract values) + 2-4 reasons tied to evidence. Missing material stays unknown."""
    env = ENV_ALIASES.get((environment or "iss").lower(), (environment or "iss").lower())
    H = habitats()
    base = H.get(env, H["iss"])
    g = gravity_g if gravity_g is not None else base["gravity_g"]
    o2 = o2 if o2 is not None else base["o2_pct"]
    p = pressure if pressure is not None else base["pressure_kpa"]
    mat = material or "unspecified material"
    reg = Registry()
    res = T.run_scenario(reg, mat, g, o2, p, flow_cm_s)
    r = res["result"]
    caveats = []
    if not material:
        caveats.append("No material was given; StarryNight does not assume one, so only general evidence is shown.")
    if fuel_type and fuel_type.lower() not in ("solid", "solid material"):
        caveats.append(f"Fuel type '{fuel_type}': the scenario engine scores solid-material tests; droplet and gas flames are shown only as atmosphere evidence.")
    verdict_line = f"VERDICT: {r['verdict']} (coverage: {_coverage(r)})"
    text, ev = L.write("scenario_reasons", f"{mat} at {g:g} g, {o2:g}% O2, {p:g} kPa", reg.block(res["evidence"]), verdict_line)
    reasons = []
    if text:
        reasons = [_clean(x.strip("-* ").strip(), reg) for x in text.splitlines() if x.strip().startswith(("-", "*"))][:4]
        reasons = [x for x in reasons if L.cited_ids(x)]
    if len(reasons) < 2:  # deterministic template reasons
        reasons, ev = _template_reasons(reg, r), ev + (["fell_back_to_template"] if text else [])
    evidence = [e.public() for e in reg.items if e.kind in ("record", "scenario", "gap", "bound", "resource")]
    return {"verdict": r["verdict"], "coverage": _coverage(r), "evidence_status": r["evidence_status"], "reasons": reasons,
            "blockers": r["blockers"], "flags": r["flags"], "evidence": evidence, "caveats": caveats,
            "gravity_bounds": r.get("gravity_bounds"),
            "scenario": {"environment": env, "material": material, "gravity_g": g, "o2_pct": o2, "pressure_kpa": p, "flow_cm_s": flow_cm_s},
            "sources": reg.sources([e["id"] for e in evidence]), "mode": _mode(ev), "guardrails": ev, "_registry": reg}


def _template_reasons(reg: Registry, r: dict) -> list[str]:
    out = []
    scen = next(e for e in reg.items if e.kind == "scenario")
    if r["blockers"]:
        out.append(f"{r['blockers'][0]} [{scen.id}]")
    solid = next((e for e in reg.items if e.kind == "record" and e.text.startswith("Closest solid")), None)
    if solid:
        out.append(f"Closest solid-material test: {solid.text.split(': ', 1)[1]} [{solid.id}]")
    atm = next((e for e in reg.items if e.kind == "record" and e.text.startswith("Closest droplet")), None) or \
        next((e for e in reg.items if e.kind == "record" and e.text.startswith("Closest gas")), None)
    if atm:
        out.append(f"Closest flames at this oxygen and pressure: {atm.text.split(': ', 1)[1]} [{atm.id}]")
    if len(r["blockers"]) > 1:
        out.append(f"{r['blockers'][1]} [{scen.id}]")
    return out[:4]


# 3. COMPARE NARRATOR ------------------------------------------------------------------------------------------
def _cond(p: dict, prefix: str) -> str:
    xs = [c for c in p["conditions"] if c["factor"].startswith(prefix)]
    if not xs:
        return "not recorded"
    c = xs[0]
    if c["kind"] == "range":
        return f"{c['min']:g}–{c['max']:g} {c['unit']}".strip()
    return ", ".join(v["value"] for v in c["values"][:4]) + (" …" if c["distinct"] > 4 else "")


def compare(ids: list[str]) -> dict:
    """Deterministic comparison table + LLM narrative from that table only. {table, narrative, sources}"""
    reg = Registry()
    res = T.compare_investigations(reg, ids)
    ps = res["profiles"]
    rows = [("Hardware", lambda p: p["hardware_family"]), ("Fuel type", lambda p: p["fuel_phase"]),
            ("Fuels / materials", lambda p: _cond(p, "Material (NASA") if _cond(p, "Material (NASA") != "not recorded" else _cond(p, "Fuel") if _cond(p, "Fuel") != "not recorded" else _cond(p, "Material")),
            ("Sample shape", lambda p: _cond(p, "Sample geometry")), ("Oxygen", lambda p: _cond(p, "Oxygen")),
            ("Pressure", lambda p: _cond(p, "Pressure")), ("Air flow", lambda p: _cond(p, "Air flow")),
            ("Sensors", lambda p: ", ".join(s["sensor"] for s in p["sensors"]) or "none named"),
            ("Measured", lambda p: ", ".join(m["sensor"] for m in p["measured_quantities"]) or "none named"),
            ("Tests in NASA table", lambda p: str(p["records"])),
            ("Outcomes recorded", lambda p: ", ".join(f"{k}: {v}" for k, v in (p["outcomes"] or {}).get("by_basis", {}).items()) or "no outcome column"),
            ("Pillar", lambda p: p["pillar"]), ("Relevance", lambda p: p["relevance_tier"])]
    table = [{"attribute": name, "values": {p["acronym"]: fn(p) for p in ps}, "differs": len({fn(p) for p in ps}) > 1} for name, fn in rows]
    tbl = reg.add("investigation", "Comparison table (computed from NASA tables): " + " | ".join(
        f"{t['attribute']}: " + "; ".join(f"{k}={v}" for k, v in t["values"].items()) for t in table),
        source_file="data/gold/analytics/investigation_profiles.json", title="StarryNight comparison table", level="analysis")
    diffs = [t["attribute"] for t in table if t["differs"]]
    same = [t["attribute"] for t in table if not t["differs"]]
    text, ev = L.write("compare", f"Compare {', '.join(p['acronym'] for p in ps)}", reg.block())
    if text is None:
        text = (f"{' and '.join(p['acronym'] for p in ps)} share: {', '.join(same) or 'none of the compared attributes'}. "
                f"They differ in: {', '.join(diffs) or 'nothing compared'} [{tbl.id}].")
    return {"table": table, "differs": diffs, "narrative": _clean(text, reg), "sources": reg.sources(), "mode": _mode(ev),
            "guardrails": ev, "_registry": reg}


# 4. GAP NARRATOR ----------------------------------------------------------------------------------------------
O2_BANDS = [(0, 18), (18, 22.5), (22.5, 26), (26, 30), (30, 36), (36, 100)]
P_BANDS = [(0, 50, "<50 kPa"), (50, 80, "50–80 kPa"), (80, 95, "80–95 kPa"), (95, 105, "~101 kPa"), (105, 1000, ">105 kPa")]
GRAVITY = [("microgravity (~0 g)", 0.0), ("Moon (0.166 g)", 0.166), ("Mars (0.38 g)", 0.38), ("Earth (1 g)", 1.0)]


def coverage_matrix() -> list[dict]:
    """fuel type x O2 band x pressure band x gravity: count of SPACE tests (all PSI flight tests are ~0 g)."""
    from .tables import table
    f = lambda x: float(x) if x not in ("", None) else None
    rows = [("solid", r.o2_initial_pct, r.pressure_kpa) for r in table("solid").itertuples()]
    rows += [("liquid droplet", r.o2_pct, r.pressure_kpa) for r in table("droplet").itertuples()]
    rows += [("liquid droplet", r.o2_pct, r.pressure_kpa) for r in table("cool_flame").itertuples()]
    rows += [("gas", r.o2_pct, r.pressure_kpa) for r in table("gas").itertuples()]
    out = []
    for fuel in ("solid", "liquid droplet", "gas"):
        for lo, hi in O2_BANDS:
            for plo, phi, plab in P_BANDS:
                n = sum(1 for k, o, p in rows if k == fuel and f(o) is not None and f(p) is not None and lo <= f(o) < hi and plo <= f(p) < phi)
                for gname, gv in GRAVITY:
                    cnt = n if gv == 0.0 else 0
                    habitat_like = lo >= 30 and phi <= 80 and gv in (0.166, 0.38)
                    out.append({"fuel_type": fuel, "o2_band": f"{lo:g}–{hi:g}%", "pressure_band": plab, "gravity": gname,
                                "space_tests": cnt, "priority": "high" if (habitat_like and fuel == "solid") else "medium" if habitat_like else "normal"})
    return out


def gaps(scenario_input: dict | None = None) -> dict:
    """Coverage gaps (deterministic) + narrative grounded in evidence. {gaps[], covered[], cells[], narrative}"""
    reg = Registry()
    res = T.research_gaps(reg)
    m = coverage_matrix()
    gap_list = [c for c in m if c["space_tests"] == 0 and c["priority"] == "high"]
    covered = [c for c in m if c["space_tests"] > 0]
    ids = list(res["evidence"])
    q = "Why the Moon/Mars solid-material gap matters"
    if scenario_input:
        s = scenario(**scenario_input)
        sreg = s.pop("_registry")
        for e in sreg.items:
            if e.kind in ("scenario", "record"):
                ids.append(reg.add(e.kind, e.text, **{k: getattr(e, k) for k in ("investigation_id", "acronym", "source_file", "source_row", "psi_url", "url", "title", "level")}).id)
        q = f"Gap for {s['scenario']}"
    hl = reg.add("gap", f"{len(gap_list)} high-priority gaps: solid materials at O2 >= 30% and pressure <= 80 kPa at Moon or Mars gravity have 0 space tests. "
                 f"{len(covered)} fuel/oxygen/pressure combinations have space data, all at ~0 g.", source_file="ai/features.py coverage_matrix() over Gold tables",
                 level="analysis")
    ids.append(hl.id)
    text, ev = L.write("gap", q, reg.block(ids))
    if text is None:
        text = (f"No solid cabin material in NASA's PSI data has been burned at O2 >= 30% and <= 80 kPa at Moon or Mars gravity [{hl.id}]. "
                f"All PSI flight tests ran at ~0 g; the closest evidence at habitat-like atmospheres is liquid-droplet and gas flames, "
                f"which are not cabin materials [{ids[0]}].")
    return {"gaps": gap_list, "covered": covered, "cells": res["cells"], "narrative": _clean(text, reg), "sources": reg.sources(),
            "mode": _mode(ev), "guardrails": ev, "_registry": reg}


# 5. WHAT BURNED SUMMARIES -------------------------------------------------------------------------------------
SUMMARY_IDS = ["PSI-25", "PSI-26", "PSI-98", "PSI-99", "PSI-100", "PSI-102", "PSI-101", "PSI-69", "PSI-107"]
_summary_cache: dict[str, dict] = {}


def experiment_summary(investigation_id: str, use_cache: bool = True) -> dict:
    """Facts from Gold tables first; LLM only rewrites. Always includes the unknown/missing caveats."""
    p = profiles().get(investigation_id.upper()) or by_acronym().get(investigation_id.upper())
    if not p:
        raise T.ToolError(f"Unknown investigation '{investigation_id}'.")
    key = p["investigation_id"]
    if use_cache and key in _summary_cache:
        return _summary_cache[key]
    reg = Registry()
    inv = T.get_investigation(reg, key, ("objective",))
    kind = {"solid": "solid", "liquid droplet": "droplet", "smoke (heated materials)": "smoke", "gas": "gas"}.get(p["fuel_phase"])
    rec = None
    if kind in ("solid", "droplet", "smoke") or key in ("PSI-159", "PSI-10"):
        try:
            rec = T.search_records(reg, kind or "gas", investigation=key, limit=3)
        except T.ToolError:
            rec = None
    mats = next((c for c in p["conditions"] if c["factor"] in ("Material family", "Material", "Fuel")), None)
    materials = ", ".join(f"{v['value']} ({v['records']})" for v in (mats or {}).get("values", [])[:6]) or "not recorded in the NASA table"
    conditions = "; ".join(f"{c['factor']} {c['min']:g}–{c['max']:g} {c['unit']}".strip() for c in p["conditions"] if c["kind"] == "range") or "not recorded"
    caveats = []
    if p["not_recorded_factors"]:
        caveats.append(f"Not recorded in the NASA table: {', '.join(p['not_recorded_factors'])}.")
    if rec and rec["basis"]:
        b = rec["basis"]
        caveats.append(f"Outcome basis: {b}. Only 'observed' outcomes were written by NASA; 'inferred' come from notes; others are unknown.")
    if p["fuel_phase"] == "solid":
        caveats.append("Pressure of these ISS/Cygnus tests is assumed cabin pressure (~101 kPa), not measured.")
        unk = sum(v["records"] for v in (mats or {}).get("values", []) if v["value"].startswith("Unknown"))
        if unk:
            caveats.append(f"{unk} samples have no material name in the NASA table (shown as Unknown, not assumed).")
    if not p["records"]:
        caveats.append("PSI holds no experimental table for this investigation (analysis or modeling study).")
    outcome = (f"{rec['total']} records; outcomes {rec['outcomes']}" if rec and rec["outcomes"] else
               f"{p['records']} records; no outcome column in the NASA table" if p["records"] else "no test records")
    facts = f"OBJECTIVE: {p['objective'][:500]}\nMATERIALS: {materials}\nCONDITIONS: {conditions}\nOUTCOMES: {outcome}\nCAVEATS: {' '.join(caveats)}"
    text, ev = L.write("experiment_summary", f"Summarize {p['acronym']}", reg.block() + "\n" + facts)
    out = {"investigation_id": key, "acronym": p["acronym"], "objective": p["objective"], "materials": materials, "conditions": conditions,
           "outcome_summary": outcome, "caveats": caveats, "narrative": _clean(text, reg) if text else None,
           "sources": reg.sources(), "mode": _mode(ev), "guardrails": ev}
    _summary_cache[key] = out
    return out


def warm_summaries() -> int:
    for i in SUMMARY_IDS:
        experiment_summary(i)
    return len(_summary_cache)


def public(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}
