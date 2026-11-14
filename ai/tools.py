"""Controlled tools: the ONLY way the AI layer reads data. Each tool calls an existing engine or Gold table and adds
Evidence items (with real source file/row, PSI URL or passage id) to the request's Registry.

Tools: search_investigations, get_investigation, search_records, rank_habitat, run_scenario, compare_investigations,
research_gaps, search_passages, list_datasets. Arguments are validated; bad arguments raise ToolError (shown as a limit).
"""
from __future__ import annotations

from collections import Counter

from . import retrieval
from .evidence import Registry
from .tables import TABLES, by_acronym, engine, habitats, profiles, table

PILLARS = ("prevention", "detection", "suppression", "fundamental")
RECORD_KINDS = ("solid", "droplet", "gas", "smoke", "cool_flame")


class ToolError(ValueError):
    pass


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _inv_evidence(reg: Registry, p: dict, field: str = "objective", level: str = "direct"):
    text = f"{p['acronym']} ({p['investigation_id']}) {field.replace('_', ' ')} (NASA PSI): {(p.get(field) or '')[:600]}"
    return reg.add("investigation", text, investigation_id=p["investigation_id"], acronym=p["acronym"], psi_url=p["psi_url"],
                   url=p["psi_url"], title=f"{p['acronym']} — {p['title']}", source_file=f"data/raw/psi/.../investigation.json ({field})",
                   level=level)


# ---------------------------------------------------------------------------------------------------------------
def search_investigations(reg: Registry, query: str, pillar: str | None = None, limit: int = 5) -> list[dict]:
    reg.used("search_investigations")
    if pillar and pillar not in PILLARS:
        raise ToolError(f"pillar must be one of {PILLARS}")
    hits = retrieval.search(query, k=30)
    seen, out = [], []
    for c in hits:
        inv = c.get("investigation_id")
        if not inv or inv in seen:
            continue
        p = profiles()[inv]
        if pillar and pillar not in (p["pillar"], p["pillar_secondary"]):
            continue
        seen.append(inv)
        e = reg.add("passage", c["text"], investigation_id=inv, acronym=p["acronym"], psi_url=p["psi_url"], url=c["url"],
                    title=c["title"], year=c.get("year"), chunk_id=c["chunk_id"],
                    level="direct" if c["content_type"] == "nasa_text" else "analysis")
        out.append({"investigation_id": inv, "acronym": p["acronym"], "pillar": p["pillar"], "tier": p["relevance_tier"], "evidence": e.id})
        if len(out) >= limit:
            break
    return out


def get_investigation(reg: Registry, investigation_id: str, sections: tuple = ("objective", "research_impacts")) -> dict:
    reg.used("get_investigation")
    p = profiles().get((investigation_id or "").upper()) or by_acronym().get((investigation_id or "").upper())
    if not p:
        raise ToolError(f"Unknown investigation '{investigation_id}'. Known: {', '.join(sorted(x['acronym'] for x in profiles().values()))}.")
    ids = [_inv_evidence(reg, p, s).id for s in sections if p.get(s)]
    cond = "; ".join(f"{c['factor']} {c['min']:g}-{c['max']:g} {c['unit']}".strip() if c["kind"] == "range"
                     else f"{c['factor']}: {', '.join(v['value'] for v in c['values'][:5])}" for c in p["conditions"])
    meta = reg.add("investigation", f"{p['acronym']} ({p['investigation_id']}): {p['study_type']} study, hardware {p['hardware_family']}, "
                   f"fuel {p['fuel_phase']}, pillar {p['pillar']}, {p['records']} records in the NASA table. Conditions: {cond or 'none recorded'}. "
                   f"Varied between tests: {', '.join(p['varied_factors']) or 'none'}. Not recorded: {', '.join(p['not_recorded_factors']) or 'none'}. "
                   f"Sensors named by NASA: {', '.join(s['sensor'] for s in p['sensors']) or 'none named'}.",
                   investigation_id=p["investigation_id"], acronym=p["acronym"], psi_url=p["psi_url"], url=p["psi_url"],
                   title=f"{p['acronym']} profile (computed from NASA tables)", source_file="data/gold/analytics/investigation_profiles.json",
                   level="analysis")
    return {"profile": p, "evidence": ids + [meta.id]}


def search_records(reg: Registry, kind: str = "solid", investigation: str | None = None, material: str | None = None,
                   o2_min: float | None = None, o2_max: float | None = None, outcome: str | None = None, limit: int = 8) -> dict:
    """Individual test rows (each with source file + row) and counts over ALL matching rows."""
    reg.used("search_records")
    if kind not in RECORD_KINDS:
        raise ToolError(f"kind must be one of {RECORD_KINDS}")
    limit = max(1, min(int(limit), 20))
    df = table(kind)
    inv_col = "investigation_id" if "investigation_id" in df.columns else "investigation"
    if investigation:
        p = profiles().get(investigation.upper()) or by_acronym().get(investigation.upper())
        if not p:
            raise ToolError(f"Unknown investigation '{investigation}'.")
        if inv_col == "investigation_id":
            df = df[df[inv_col] == p["investigation_id"]]
        elif kind == "droplet":
            df = df if p["investigation_id"] == "PSI-69" else df.iloc[0:0]
        elif kind == "cool_flame":
            df = df if p["investigation_id"] == "PSI-39" else df.iloc[0:0]
        else:
            df = df[df[inv_col] == p["acronym"]]
    if material:
        m = material.lower()
        cols = [c for c in ("material_family_effective", "material_raw", "material", "fuel") if c in df.columns]
        df = df[df[cols].apply(lambda r: any(m in str(v).lower() for v in r), axis=1)] if cols else df
    o2c = next((c for c in ("o2_initial_pct", "o2_pct") if c in df.columns), None)
    if o2c and (o2_min is not None or o2_max is not None):
        v = df[o2c].map(_f)
        df = df[v.notna() & (v >= (o2_min if o2_min is not None else -1)) & (v <= (o2_max if o2_max is not None else 101))]
    if outcome and "outcome_class" in df.columns:
        df = df[df["outcome_class"].str.lower() == outcome.lower()]
    counts = dict(Counter(df["outcome_class"])) if "outcome_class" in df.columns else {}
    basis = dict(Counter(df["outcome_basis"])) if "outcome_basis" in df.columns else {}
    ids = []
    for _, r in df.head(limit).iterrows():
        bits = [f"{k}={r[k]}" for k in ("investigation", "material_raw", "material", "fuel", "geometry", "o2_initial_pct", "o2_pct",
                                        "pressure_kpa", "pressure_status", "flow_min_cm_s", "flow_cm_s", "diluent", "outcome_class",
                                        "outcome_basis") if k in r and r[k] != ""]
        inv_id = r.get("investigation_id") or ("PSI-69" if kind == "droplet" else "PSI-39" if kind == "cool_flame" else None)
        acr = profiles()[inv_id]["acronym"] if inv_id in profiles() else r.get("investigation")
        e = reg.add("record", f"Test {r.get('test_id') or r.get('record_id')}: " + ", ".join(bits), investigation_id=inv_id, acronym=acr,
                    source_file=r["source_file"], source_row=int(float(r["source_row"])) if r.get("source_row") else None,
                    psi_url=r.get("psi_url") or None, url=r.get("psi_url") or None, title=f"{acr} test record")
        ids.append(e.id)
    summary = None
    if len(df):
        summary = reg.add("table", f"{len(df)} matching {kind} records"
                          + (f" in {investigation}" if investigation else "") + (f" for '{material}'" if material else "")
                          + (f"; outcomes {counts}" if counts else "") + (f"; outcome basis {basis}" if basis else "")
                          + f". Counts computed over data/gold/{TABLES[kind]}.", source_file=f"data/gold/{TABLES[kind]}", level="analysis").id
    return {"total": int(len(df)), "outcomes": counts, "basis": basis, "evidence": ids, "summary": summary}


def rank_habitat(reg: Registry, habitat: str = "moon", pillar: str | None = None, top: int = 5) -> dict:
    reg.used("rank_habitat")
    from backend.ranking import rank
    H = habitats()
    if habitat not in H:
        raise ToolError(f"habitat must be one of {sorted(H)}")
    if pillar and pillar not in PILLARS:
        raise ToolError(f"pillar must be one of {PILLARS}")
    hab = {k: v for k, v in H[habitat].items() if k != "in_missions"}
    rows = rank(list(profiles().values()), hab, pillar)[: max(1, min(int(top), 24))]
    ids = []
    for r in rows:
        e = reg.add("ranking", f"Rank {r['rank']} for {hab['name']} ({hab['o2_pct']:g}% O2, {hab['pressure_kpa']:g} kPa, {hab['gravity_g']:g} g): "
                    f"{r['acronym']} score {r['score']:.0f}/100. " + " ".join(r["reasons"][:3]),
                    investigation_id=r["investigation_id"], acronym=r["acronym"], psi_url=r["psi_url"], url=r["psi_url"],
                    title=f"StarryNight habitat ranking ({habitat})", source_file="backend/ranking.py (computed)", level="analysis")
        ids.append(e.id)
    return {"habitat": hab, "ranked": rows, "evidence": ids}


def run_scenario(reg: Registry, material: str, gravity_g: float, o2_pct: float, pressure_kpa: float, flow_cm_s: float = 5.0) -> dict:
    """The existing scenario engine decides the verdict. Never overridden."""
    reg.used("run_scenario")
    for name, v, lo, hi in (("gravity_g", gravity_g, 0, 1.5), ("o2_pct", o2_pct, 0, 100), ("pressure_kpa", pressure_kpa, 1, 600),
                            ("flow_cm_s", flow_cm_s, 0, 200)):
        if v is None or not lo <= float(v) <= hi:
            raise ToolError(f"{name}={v} is outside {lo}-{hi}")
    r = engine().scenario(material, float(gravity_g), float(o2_pct), float(pressure_kpa), float(flow_cm_s))
    ids = []
    v = reg.add("scenario", f"Scenario engine verdict for {material} at {gravity_g:g} g, {o2_pct:g}% O2, {pressure_kpa:g} kPa, "
                f"{flow_cm_s:g} cm/s: '{r['verdict']}' (evidence status {r['evidence_status']}). "
                + ("Blockers: " + " ".join(r["blockers"]) if r["blockers"] else "No blockers."),
                source_file="backend/engine.py (deterministic rules over gold/analytics/solid_fire_tests.csv)", level="analysis")
    ids.append(v.id)
    for t in r["evidence"]:
        e = reg.add("record", f"Closest solid test {t['test_id']} ({t['investigation']}): {t['material']} [{t['material_identity']}], "
                    f"{t['o2_pct']}% O2, {t['pressure_kpa']} kPa ({t['pressure_status']}), {t['gravity_g']} g, flow {t['flow_cm_s']} cm/s, "
                    f"outcome {t['outcome']} ({t['outcome_basis']}); biggest difference: {t['biggest_difference']}.",
                    investigation_id=next((p["investigation_id"] for p in profiles().values() if p["acronym"] == t["investigation"]), None),
                    acronym=t["investigation"], source_file=t["source_file"], source_row=int(t["source_row"]), psi_url=t["psi_url"],
                    url=t["psi_url"], title=f"{t['investigation']} test record", level="related")
        ids.append(e.id)
    for a in r.get("atmosphere_evidence", []):
        e = reg.add("record", f"Closest {a['kind']} at this atmosphere, {a['test_id']} ({a['investigation']}): {a['fuel']}, {a['o2_pct']}% O2, "
                    f"{a['pressure_kpa']} kPa, ~0 g, outcome {a['outcome']} ({a['outcome_basis']}). {a['note']}",
                    investigation_id=next((p["investigation_id"] for p in profiles().values() if p["acronym"] == a["investigation"]), None),
                    acronym=a["investigation"], source_file=a["source_file"], source_row=int(a["source_row"]), psi_url=a["psi_url"],
                    url=a["psi_url"], title=f"{a['investigation']} test record", level="related")
        ids.append(e.id)
    b = r.get("gravity_bounds")
    if b:
        lo, up = b["lower_bound"], b["upper_bound"]
        ids.append(reg.add("bound", f"0 g bound for {material}: {lo['tests']} microgravity tests, outcomes {lo['outcomes']} "
                           f"(basis {lo.get('outcome_basis', {})})" + (f", O2 {lo['o2_range'][0]:g}-{lo['o2_range'][1]:g}%" if lo["o2_range"] else "")
                           + f", pressure {lo['pressure']}." + (f" {lo['note']}" if lo["note"] else ""),
                           source_file="backend/engine.py gravity_bounds() over gold/analytics/solid_fire_tests.csv", level="analysis").id)
        for pr in up["pairs"][:4]:
            ids.append(reg.add("record", f"1 g bound, NASA Saffire-II comparison {pr['test_id']}: {pr['material']} at {pr['o2_pct']}% O2, "
                               f"burn length in microgravity {pr['microgravity_burn_length']} vs at 1 g {pr['one_g_burn_length']}.",
                               investigation_id="PSI-99", acronym="SAFFIRE-II", source_file=pr["source_file"],
                               source_row=int(pr["source_row"]), psi_url=pr["psi_url"], url=pr["psi_url"],
                               title="SAFFIRE-II 1 g comparison", level="direct").id)
        if up["note"]:
            ids.append(reg.add("bound", f"1 g bound: {up['note']}", source_file="backend/engine.py gravity_bounds()", level="analysis").id)
        ids.append(reg.add("bound", f"Do the bounds cover this request? {b['applies']}", source_file="backend/engine.py gravity_bounds()",
                           level="analysis").id)
        ids.append(reg.add("resource", b["partial_gravity_mimic"]["text"], url=b["partial_gravity_mimic"]["url"],
                           psi_url=b["partial_gravity_mimic"]["url"], investigation_id="PSI-22", acronym="ACME E-FIELD",
                           title="E-FIELD Flames: partial-gravity mimic", level="related").id)
    for w in r.get("why_untested", []):
        ids.append(reg.add("gap", w["text"], url=w["source_url"], psi_url=w["source_url"], title=f"Why untested: {w['topic']}",
                           source_file="backend/engine.py WHY (from PSI coverage)", level="analysis").id)
    return {"result": r, "evidence": ids}


def compare_investigations(reg: Registry, ids: list[str]) -> dict:
    reg.used("compare_investigations")
    from backend.compare import compare_profiles
    ps = []
    for i in ids:
        p = profiles().get(str(i).upper()) or by_acronym().get(str(i).upper())
        if not p:
            raise ToolError(f"Unknown investigation '{i}'.")
        if p not in ps:
            ps.append(p)
    if not 2 <= len(ps) <= 6:
        raise ToolError("Compare needs 2 to 6 distinct investigations.")
    c = compare_profiles(ps)
    ev = [get_investigation(reg, p["investigation_id"], ("objective",))["evidence"] for p in ps]
    return {"comparison": c, "profiles": ps, "evidence": [x for e in ev for x in e]}


def research_gaps(reg: Registry, habitat: str | None = None) -> dict:
    reg.used("research_gaps")
    cells = engine().gaps()
    tested = [c for c in cells if c["space_tests"]]
    flames_only = [c for c in cells if not c["space_tests"] and (c["gas_flame_tests"] or c["droplet_tests"])]
    empty = [c for c in cells if not (c["space_tests"] or c["gas_flame_tests"] or c["droplet_tests"])]
    pins = [c for c in cells if c["mission_design_points"]]
    ids = [reg.add("gap", f"Coverage grid (gravity x O2 band x pressure band, {len(cells)} cells): {len(tested)} cells have solid-material space "
                   f"tests, {len(flames_only)} have only gas/droplet flames, {len(empty)} have no space combustion data. All solid tests are at ~0 g "
                   "and assumed cabin pressure (~101 kPa).", source_file="backend/engine.py gaps() over gold/analytics", level="analysis").id]
    for c in pins:
        ids.append(reg.add("gap", f"Design point(s) {', '.join(c['mission_design_points'])}: gravity {c['gravity_g']} g, O2 {c['o2_range']}, "
                           f"pressure {c['pressure']}: {c['space_tests']} solid space tests, {c['gas_flame_tests']} gas-flame and "
                           f"{c['droplet_tests']} droplet tests.", source_file="backend/engine.py gaps()", level="analysis").id)
    pg = [x for x in retrieval.search("partial gravity LUCI FM2 E-FIELD bound", k=3, content_type="challenge_resource")]
    for c in pg:
        ids.append(reg.add("resource", c["text"], url=c["url"], title=c["title"], year=c.get("year"), chunk_id=c["chunk_id"], level="related").id)
    return {"cells": cells, "evidence": ids, "tested": len(tested), "flames_only": len(flames_only), "empty": len(empty)}


def search_passages(reg: Registry, query: str, k: int = 6, investigation: str | None = None, content_type: str | None = None) -> list[str]:
    reg.used("search_passages")
    ids = []
    for c in retrieval.search(query, k=max(1, min(int(k), 10)), investigation=investigation, content_type=content_type):
        lvl = {"nasa_text": "direct", "computed_summary": "analysis", "challenge_resource": "related"}[c["content_type"]]
        ids.append(reg.add("resource" if c["content_type"] == "challenge_resource" else "passage", c["text"],
                           investigation_id=c.get("investigation_id"), acronym=c.get("acronym"), url=c["url"],
                           psi_url=c["url"] if c.get("investigation_id") else None, title=c["title"], year=c.get("year"),
                           chunk_id=c["chunk_id"], level=lvl).id)
    return ids


def list_datasets(reg: Registry) -> list[str]:
    """Datasets for predictive modeling: real columns and row counts, plus their caveats."""
    reg.used("list_datasets")
    ids = []
    notes = {
        "ml": "ML-ready table of solid space tests; label = burned (observed outcomes only); NOT validated (baseline below majority class).",
        "solid": "Solid-material space tests (BASS, BASS-II, Saffire I-III). Pressure is assumed cabin (~101 kPa), not measured; most outcomes inferred.",
        "droplet": "FLEX droplet flames: oxygen, measured pressure, diluent (N2/CO2/He), extinction diameter, burn time; outcomes written by NASA.",
        "gas": "ACME gas flames (CFI-G, Flame Design): oxygen 12-85%, pressure; CFI-G outcomes are NASA codes.",
        "smoke": "SAME / SAME-R smoke from heated materials: air flow, heater setting, aging time. No burning.",
    }
    for k, note in notes.items():
        df = table(k)
        cols = ", ".join(df.columns[:18]) + (" ..." if len(df.columns) > 18 else "")
        ids.append(reg.add("dataset", f"Dataset data/gold/{TABLES[k]}: {len(df)} rows; columns: {cols}. {note}",
                           source_file=f"data/gold/{TABLES[k]}", level="analysis").id)
    return ids
