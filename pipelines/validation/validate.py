"""Validate Bronze, Silver, Gold, RAG and quarantine outputs. Exits 1 if any ERROR is found.

Also writes the machine-readable JSON Schemas (schemas/) and the reports:
docs/DATA_QUALITY_REPORT.md, docs/PROVENANCE_REPORT.md
"""
import csv, json, sys
from collections import Counter
from pipelines.common import ROOT, SILVER, GOLD, QUAR, MANIFESTS, SCHEMAS, DOCS, OUTCOME_CLASSES, OUTCOME_BASIS, sha256, RUN_TS

N, S, I, B = "number", "string", "integer", "boolean"
COMMON = {"record_id": S, "investigation_id": S, "investigation": S, "source_file": S, "source_row": I, "source_record": S,
          "quality_status": S, "quality_notes": S}
SPEC = {  # table -> (layer path, {column: type}, required columns, ranges)
    "silver/bass2_tests": ("silver/investigations/bass2_tests.csv", {**COMMON, "material_id": S, "o2_initial_pct": N, "o2_final_pct": N,
                           "flow_start_cm_s": N, "flow_min_cm_s": N, "pressure_kpa": N, "thickness_mm": N, "diameter_mm": N,
                           "outcome_class": S, "outcome_basis": S}, ["record_id", "material_id", "outcome_class", "outcome_basis"],
                           {"o2_initial_pct": (0, 100), "flow_min_cm_s": (0, 100), "pressure_kpa": (1, 500)}),
    "silver/bass_tests": ("silver/investigations/bass_tests.csv", {**COMMON, "material_id": S, "outcome_class": S, "outcome_basis": S}, ["record_id", "material_id"], {}),
    "silver/saffire1_tests": ("silver/investigations/saffire1_tests.csv", {**COMMON, "material_id": S, "o2_initial_pct": N, "flow_cm_s": N, "thickness_mm": N, "burn_time_s": N, "outcome_class": S, "outcome_basis": S}, ["record_id", "material_id"], {"o2_initial_pct": (0, 100)}),
    "silver/saffire2_tests": ("silver/investigations/saffire2_tests.csv", {**COMMON, "material_id": S, "o2_initial_pct": N, "flow_cm_s": N, "thickness_mm": N, "outcome_class": S, "outcome_basis": S}, ["record_id", "material_id"], {"o2_initial_pct": (0, 100)}),
    "silver/saffire3_tests": ("silver/investigations/saffire3_tests.csv", {**COMMON, "material_id": S, "flow_cm_s": N, "thickness_mm": N, "outcome_class": S, "outcome_basis": S}, ["record_id", "material_id"], {}),
    "silver/same_smoke_tests": ("silver/investigations/same_smoke_tests.csv", {**COMMON, "material_id": S, "flow_cm_s": N, "weight_loss_rate_mg_min": N}, ["record_id", "material_id"], {}),
    "silver/same_r_smoke_tests": ("silver/investigations/same_r_smoke_tests.csv", {**COMMON, "material_id": S, "inlet_velocity_cm_s": N, "heater_resistance_ratio": N, "net_aging_time_s": N}, ["record_id", "material_id"], {"inlet_velocity_cm_s": (0, 100)}),
    "silver/flex_droplet_tests": ("silver/investigations/flex_droplet_tests.csv", {**COMMON, "material_id": S, "pressure_kpa": N, "o2_pct": N, "droplet_initial_diameter_mm": N, "extinction_diameter_mm": N, "burn_time_s": N, "outcome_class": S, "outcome_basis": S}, ["record_id", "material_id", "fuel"], {"o2_pct": (0, 100), "pressure_kpa": (1, 500)}),
    "silver/spice_flames": ("silver/investigations/spice_flames.csv", {**COMMON, "material_id": S, "nozzle_diameter_mm": N, "fuel_rate_mg_s": N, "air_velocity_cm_s": N}, ["record_id", "material_id", "fuel"], {"air_velocity_cm_s": (0, 200)}),
    "silver/materials": ("silver/materials/materials.csv", {"material_id": S, "material_normalized_name": S, "material_family": S, "candidate_family": S, "classification_basis": S, "classification_confidence": S}, ["material_id", "material_family", "classification_basis"], {}),
    "silver/material_samples": ("silver/materials/material_samples.csv", {"sample_id": S, "record_id": S, "material_id": S, "source_file": S, "source_row": I}, ["sample_id", "record_id", "material_id"], {}),
    "silver/material_properties": ("silver/materials/material_properties.csv", {"property_id": S, "sample_id": S, "material_id": S, "property": S, "value": S, "unit": S, "value_status": S}, ["property_id", "sample_id", "property", "value_status"], {}),
    "silver/measurements": ("silver/measurements/measurements.csv", {"measurement_id": S, "record_id": S, "quantity": S, "value": N, "unit": S, "value_status": S, "source_file": S, "source_row": I}, ["measurement_id", "record_id", "quantity", "value", "unit"], {}),
    "gold/solid_fire_tests": ("gold/analytics/solid_fire_tests.csv", {"test_id": S, "material_id": S, "o2_initial_pct": N, "flow_min_cm_s": N, "pressure_kpa": N, "outcome_class": S, "outcome_basis": S, "label_reliable": S, "source_file": S, "source_row": I}, ["test_id", "material_id", "outcome_class", "outcome_basis", "source_file", "source_row"], {"o2_initial_pct": (0, 100)}),
    "gold/droplet_extinction_tests": ("gold/analytics/droplet_extinction_tests.csv", {"test_id": S, "pressure_kpa": N, "o2_pct": N, "outcome_class": S, "source_file": S, "source_row": I}, ["test_id", "source_file", "source_row"], {}),
    "gold/gas_jet_flame_conditions": ("gold/analytics/gas_jet_flame_conditions.csv", {"record_id": S, "fuel_rate_mg_s": N, "air_velocity_cm_s": N, "source_file": S, "source_row": I}, ["record_id", "source_file"], {}),
    "gold/smoke_generation_tests": ("gold/analytics/smoke_generation_tests.csv", {"record_id": S, "investigation": S, "flow_cm_s": N, "source_file": S, "source_row": I}, ["record_id", "source_file"], {}),
    "silver/cfi_cool_flame_tests": ("silver/investigations/cfi_cool_flame_tests.csv", {**COMMON, "material_id": S, "pressure_kpa": N, "o2_pct": N, "n2_pct": N, "he_pct": N, "outcome_class": S, "outcome_basis": S}, ["record_id", "material_id", "fuel"], {"o2_pct": (0, 100), "pressure_kpa": (1, 600)}),
    "silver/flex2_test_matrix": ("silver/investigations/flex2_test_matrix.csv", {**COMMON, "o2_min_pct": N, "o2_max_pct": N, "pressure_min_kpa": N, "pressure_max_kpa": N}, ["record_id", "fuel", "row_type"], {"o2_max_pct": (0, 100), "pressure_max_kpa": (1, 600)}),
    "gold/cool_flame_tests": ("gold/analytics/cool_flame_tests.csv", {"test_id": S, "pressure_kpa": N, "o2_pct": N, "outcome_class": S, "outcome_basis": S, "source_file": S}, ["test_id", "fuel", "source_file", "source_row"], {"o2_pct": (0, 100), "pressure_kpa": (1, 600)}),
    "silver/acme_cfig_tests": ("silver/investigations/acme_cfig_tests.csv", {**COMMON, "o2_pct": N, "pressure_kpa": N, "burn_time_s": N, "outcome_class": S, "outcome_basis": S}, ["record_id", "fuel", "test", "outcome_class"], {"o2_pct": (0, 100), "pressure_kpa": (1, 600)}),
    "silver/acme_flame_design_tests": ("silver/investigations/acme_flame_design_tests.csv", {**COMMON, "o2_pct": N, "pressure_kpa": N, "outcome_class": S, "outcome_basis": S}, ["record_id", "fuel", "test"], {"o2_pct": (0, 100), "pressure_kpa": (1, 600)}),
    "silver/acme_bre_sessions": ("silver/investigations/acme_bre_sessions.csv", {**COMMON, "o2_max_pct": N, "flames_ignited": N}, ["record_id", "row_type", "fuel"], {"o2_max_pct": (0, 100)}),
    "silver/psi_session_logs": ("silver/investigations/psi_session_logs.csv", {**COMMON, "flames_ignited": N}, ["record_id", "row_type"], {}),
    "gold/gas_flame_tests": ("gold/analytics/gas_flame_tests.csv", {"test_id": S, "o2_pct": N, "pressure_kpa": N, "outcome_class": S, "outcome_basis": S, "source_file": S}, ["test_id", "investigation", "fuel", "source_file", "source_row"], {"o2_pct": (0, 100), "pressure_kpa": (1, 600)}),
    "gold/mission_coverage": ("gold/analytics/mission_coverage.csv", {"mission": S, "space_solid_tests_near": I}, ["mission"], {}),
    "gold/kpis": ("gold/powerbi/kpis.csv", {"kpi": S, "formula": S, "value": S, "unit": S}, ["kpi", "formula", "value"], {}),
    "gold/ml_solid_outcome_features": ("gold/ml/solid_outcome_features.csv", {"test_id": S, "o2_initial_pct": N, "flow_min_cm_s": N, "target_burned": I, "split": S}, ["test_id", "target_burned", "split", "label_source"], {}),
    "quarantine": ("quarantine/quarantine.csv", {"original_record": S, "source_file": S, "investigation": S, "failure_reason": S, "validation_rule": S, "processed_at": S}, ["original_record", "source_file", "failure_reason", "validation_rule", "processed_at"], {}),
}

errors, warns, info = [], [], []


def load(path):
    with open(ROOT / "data" / path, encoding="utf-8") as f: return list(csv.DictReader(f))


def typed(v, t):
    if v in ("", None): return True
    try:
        if t == N: float(v)
        elif t == I: int(float(v)); assert float(v).is_integer()
        return True
    except Exception:
        return False


def write_schemas():
    jt = {N: ["number", "null"], I: ["integer", "null"], S: ["string", "null"], B: ["boolean", "null"]}
    for name, (path, cols, req, rng) in SPEC.items():
        props = {c: {"type": jt[t]} for c, t in cols.items()}
        for c, (lo, hi) in rng.items(): props[c].update(minimum=lo, maximum=hi)
        sch = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": f"astrofire/{name}", "title": name,
               "description": f"Row schema for data/{path}", "type": "object", "properties": props, "required": req}
        p = SCHEMAS / (name.split("/")[0] if "/" in name else "quality") / f"{name.split('/')[-1]}.schema.json"
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(sch, indent=2))


def check_tables():
    tables = {}
    for name, (path, cols, req, rng) in SPEC.items():
        fp = ROOT / "data" / path
        if not fp.exists(): errors.append(f"{name}: output missing ({path})"); continue
        rows = load(path); tables[name] = rows
        if not rows: errors.append(f"{name}: empty"); continue
        missing_cols = [c for c in req if c not in rows[0]]
        if missing_cols: errors.append(f"{name}: missing required columns {missing_cols}")
        for c in req:
            n = sum(1 for r in rows if r.get(c, "") == "")
            if n: errors.append(f"{name}: {n} rows with empty required '{c}'")
        for c, t in cols.items():
            if c not in rows[0]: continue
            bad = sum(1 for r in rows if not typed(r[c], t))
            if bad: errors.append(f"{name}: {bad} values in '{c}' are not {t}")
        for c, (lo, hi) in rng.items():
            if c not in rows[0]: continue
            bad = [r[c] for r in rows if r[c] not in ("", None) and typed(r[c], N) and not lo <= float(r[c]) <= hi]
            if bad: errors.append(f"{name}: {len(bad)} '{c}' values outside [{lo},{hi}]")
        key = next((k for k in ("measurement_id", "property_id", "sample_id", "record_id", "test_id", "material_id", "kpi") if k in rows[0]), None)
        if key and name != "quarantine":
            d = [k for k, v in Counter(r[key] for r in rows).items() if v > 1]
            if d: errors.append(f"{name}: {len(d)} duplicate {key} values, e.g. {d[:3]}")
        for c, allowed in (("outcome_class", OUTCOME_CLASSES), ("outcome_basis", OUTCOME_BASIS)):
            if c in rows[0]:
                bad = {r[c] for r in rows if r[c] and r[c] not in allowed}
                if bad: errors.append(f"{name}: unknown {c} values {bad}")
        info.append(f"{name}: {len(rows)} rows OK-checked")
    return tables


def check_integrity(t):
    mats = {r["material_id"] for r in t.get("silver/materials", [])}
    recs = set()
    for n, rows in t.items():
        if n.startswith("silver/") and rows and "source_record" in rows[0]: recs |= {r["record_id"] for r in rows}
    samples = t.get("silver/material_samples", [])
    for name, rows, col, ref in [("material_samples.material_id", samples, "material_id", mats),
                                 ("material_samples.record_id", samples, "record_id", recs),
                                 ("measurements.record_id", t.get("silver/measurements", []), "record_id", recs),
                                 ("material_properties.sample_id", t.get("silver/material_properties", []), "sample_id", {s["sample_id"] for s in samples}),
                                 ("gold.solid_fire_tests.test_id", t.get("gold/solid_fire_tests", []), "test_id", recs),
                                 ("gold.solid_fire_tests.material_id", t.get("gold/solid_fire_tests", []), "material_id", mats)]:
        bad = [r[col] for r in rows if r[col] not in ref]
        (errors if bad else info).append(f"FK {name}: {len(bad)} orphans" + (f" e.g. {bad[:3]}" if bad else ""))
    ml = t.get("gold/ml_solid_outcome_features", [])
    if any(r["label_source"] != "observed (NASA note)" for r in ml): errors.append("ML table contains non-observed labels")
    inferred_as_reliable = [r for r in t.get("gold/solid_fire_tests", []) if r["outcome_basis"] != "observed" and r["label_reliable"] == "True"]
    if inferred_as_reliable: errors.append(f"{len(inferred_as_reliable)} inferred outcomes marked label_reliable")
    for name, rows in t.items():
        if name.startswith("silver/") and rows and "source_record" in rows[0]:
            if any(not r["source_file"] or not r["source_row"] for r in rows): errors.append(f"{name}: record without provenance")


def check_bronze():
    mf = MANIFESTS / "bronze_manifest.csv"
    if not mf.exists(): errors.append("bronze manifest missing"); return []
    rows = list(csv.DictReader(open(mf, encoding="utf-8"))); changed = []
    for r in rows:
        p = ROOT / r["path"]
        if not p.exists(): errors.append(f"bronze file missing: {r['path']}")
        elif sha256(p) != r["sha256"]: changed.append(r["path"])
    if changed: errors.append(f"bronze files changed since manifest (raw data must be immutable): {changed[:5]}")
    used = set()
    for path in ("silver/investigations/" + n + ".csv" for n in ("bass2_tests", "flex_droplet_tests", "spice_flames", "same_r_smoke_tests",
                                                                 "same_smoke_tests", "saffire1_tests", "saffire2_tests", "saffire3_tests", "bass_tests")):
        used |= {r["source_file"] for r in load(path)}
    known = {r["path"] for r in rows}
    for u in used:
        (info if u in known else errors).append(f"provenance: {u} {'in manifest' if u in known else 'NOT in bronze manifest'}")
    return rows


def check_rag():
    docs = [json.loads(l) for l in open(GOLD / "rag" / "documents.jsonl", encoding="utf-8")]
    ch = [json.loads(l) for l in open(GOLD / "rag" / "chunks.jsonl", encoding="utf-8")]
    ids = {d["document_id"] for d in docs}
    if len({c["chunk_id"] for c in ch}) != len(ch): errors.append("rag: duplicate chunk_id")
    orphan = sum(c["document_id"] not in ids for c in ch)
    if orphan: errors.append(f"rag: {orphan} chunks without document")
    if any(not c["url"] for c in ch): errors.append("rag: chunks without source url")
    bad = [c["chunk_id"] for c in ch if c.get("content_type") not in ("nasa_text", "computed_summary", "challenge_resource")]
    if bad: errors.append(f"rag: {len(bad)} chunks with unknown content_type (e.g. {bad[0]})")
    if any("ntrs" in (c.get("url") or "") for c in ch): errors.append("rag: NTRS paper in PSI-only knowledge base")
    info.append(f"rag: {len(docs)} documents, {len(ch)} chunks, all with url + document_id")
    return docs, ch


def reports(bronze, tables, docs, ch):
    q = tables.get("quarantine", [])
    qc = Counter((r["investigation"], r["validation_rule"], r["severity"]) for r in q)
    lines = [f"# Data Quality Report", "", f"Generated by `pipelines/validation/validate.py` at {RUN_TS}. Regenerated on every pipeline run.", "",
             f"**Result: {'PASS' if not errors else 'FAIL'}** — {len(errors)} errors, {len(warns)} warnings.", "", "## Errors", ""]
    lines += [f"- {e}" for e in errors] or ["- none"]
    lines += ["", "## Silver record quality", "", "| table | records | valid | with warnings |", "|---|---|---|---|"]
    for n, rows in tables.items():
        if n.startswith("silver/") and rows and "quality_status" in rows[0]:
            lines.append(f"| {n} | {len(rows)} | {sum(r['quality_status']=='valid' for r in rows)} | {sum(r['quality_status']=='warning' for r in rows)} |")
    lines += ["", "## Quarantine (nothing deleted; see data/quarantine/quarantine.csv)", "", "| investigation | rule | severity | records |", "|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c} | {n} |" for (a, b, c), n in sorted(qc.items())]
    sol = tables.get("gold/solid_fire_tests", [])
    lines += ["", "## Evidence limits (read before using any number)", "",
              f"- Outcome basis in solid fire tests: {dict(Counter(r['outcome_basis'] for r in sol))}. Only `observed` is ground truth.",
              f"- Material identity: {dict(Counter(r['material_identity'] for r in sol))}.",
              "- Pressure for every ISS/Cygnus solid test is **assumed** 101.3 kPa (not in NASA tables). FLEX pressure is measured.",
              "- SAME-R and SPICE dates lack the year; FLEX/BASS/BASS-II dates are complete.",
              "- No material density, mass, composition or thermal properties exist in these NASA tables; they are left empty, not estimated.",
              "- FLEX header subscripts were restored (O→O2, N→N2, CO→CO2). FLEX 'Burning rate; mm' keeps NASA's unit label unchanged.",
              "", "## Checks run", ""] + [f"- {x}" for x in info]
    (DOCS / "DATA_QUALITY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    by_src = Counter(r["source_system"] for r in bronze)
    pv = ["# Provenance Report", "", f"Generated at {RUN_TS} from `data/manifests/bronze_manifest.csv`.", "",
          "Every Silver record has `source_file` + `source_row` (+ the full original row in `source_record`). Every Gold row keeps `source_file` + `source_row`. Every knowledge-base passage has `document_id`, `url`, `content_type` (nasa_text / computed_summary / challenge_resource); PSI documents carry the SHA-256 of their investigation.json.", "",
          "| source system | files |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(by_src.items())]
    pv += ["", "## Experiment tables used (SHA-256)", "", "| file | sha256 (first 16) | source url |", "|---|---|---|"]
    for r in bronze:
        if "Experimental table" in r["path"]: pv.append(f"| {r['path'].split('/')[-1]} | {r['sha256'][:16]} | {r['source_url']} |")
    pv += ["", f"AI knowledge base (PSI only): {len(docs)} documents, {len(ch)} passages."]
    (DOCS / "PROVENANCE_REPORT.md").write_text("\n".join(pv) + "\n", encoding="utf-8")


def main():
    write_schemas()
    bronze = check_bronze(); tables = check_tables(); check_integrity(tables); docs, ch = check_rag()
    reports(bronze, tables, docs, ch)
    print(f"validation: {'PASS' if not errors else 'FAIL'} | errors {len(errors)} | checks {len(info)}")
    for e in errors: print("  ERROR", e)
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
