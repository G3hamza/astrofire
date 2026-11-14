"""Gold layer: analytics-ready tables. Built only from Silver (PSI data only).

gold/analytics/   one table per compatible family of experiments (no forced merge of incompatible ones)
gold/powerbi/     overview tables + KPI definitions with computed values
gold/ml/          ML-ready table ONLY for solid flame tests with observed labels, plus split column
gold/rag/         documents.jsonl + chunks.jsonl with provenance (built by rag.py)
"""
import csv, hashlib, json
from collections import Counter, defaultdict
from pipelines.common import SILVER, GOLD, PROCESSED, ROOT, INVESTIGATIONS, write_csv, investigation_json, psi_url, RUN_TS, ISS_KPA, HABITATS

MISSIONS = {h["name"]: dict(gravity_g=h["gravity_g"], o2_pct=h["o2_pct"], pressure_kpa=h["pressure_kpa"])
            for h in HABITATS.values() if h["in_missions"]}  # single definition: pipelines/common.HABITATS


def load(name, sub="investigations"):
    with open(SILVER / sub / f"{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def f(x):
    try: return float(x)
    except (TypeError, ValueError): return None


def solid_fire_tests():
    rows = []
    for name in ("bass2_tests", "bass_tests", "saffire1_tests", "saffire2_tests", "saffire3_tests"):
        for r in load(name):
            fam = r["material_family"]; named = r["classification_basis"] == "explicit_name"
            o2 = r.get("o2_initial_pct") or ""
            flow_min = r.get("flow_min_cm_s") or r.get("flow_cm_s") or ""
            flow_start = r.get("flow_start_cm_s") or r.get("flow_cm_s") or ""
            rows.append(dict(
                test_id=r["record_id"], investigation_id=r["investigation_id"], investigation=r["investigation"],
                platform=INVESTIGATIONS[r["investigation_id"]]["platform"], gravity_g=0.0,
                material_id=r["material_id"], material_raw=r["material_original_name"], material_family=fam,
                material_family_effective=fam if named else (r.get("candidate_family") or "Unknown"),
                material_identity="named in NASA table" if named else "not named; family inferred from investigation context" if r.get("candidate_family") else "unknown",
                geometry=r.get("geometry", ""), thickness_mm=r.get("thickness_mm", ""), diameter_mm=r.get("diameter_mm", ""),
                o2_initial_pct=o2, o2_final_pct=r.get("o2_final_pct", ""),
                pressure_kpa=r.get("pressure_kpa") or ISS_KPA, pressure_status=r.get("pressure_status", ""),
                flow_start_cm_s=flow_start, flow_min_cm_s=flow_min, flow_direction=r.get("flow_direction", ""),
                outcome_class=r["outcome_class"], outcome_basis=r["outcome_basis"],
                label_reliable=r["outcome_basis"] == "observed",
                burn_time_s=r.get("burn_time_s", ""), ug_burn_length=r.get("ug_burn_length_raw", ""), one_g_burn_length=r.get("one_g_burn_length_raw", ""),
                test_date=r.get("test_date", ""), quality_status=r["quality_status"], quality_notes=r["quality_notes"],
                notes_raw=(f"air display: {r.get('air_display_raw','')} | fan: {r.get('fan_display_raw','')}" if r["investigation"] == "BASS-II"
                           else r["source_record"][:300]),
                source_file=r["source_file"], source_row=r["source_row"], psi_url=psi_url(r["investigation_id"]),
                doi=investigation_json(r["investigation_id"]).get("doi", "")))
    return rows


def droplet_tests():
    return [dict(test_id=r["record_id"], fuel=r["fuel"], material_id=r["material_id"], test_date=r["test_date"],
                 pressure_kpa=r["pressure_kpa"], o2_pct=r["o2_pct"], n2_pct=r["n2_pct"], co2_pct=r["co2_pct"], he_pct=r["he_pct"],
                 diluent=("CO2" if (f(r["co2_pct"]) or 0) > 0 else "He" if (f(r["he_pct"]) or 0) > 0 else "N2 (air-like)"),
                 droplet_initial_diameter_mm=r["droplet_initial_diameter_mm"], extinction_diameter_mm=r["extinction_diameter_mm"],
                 burn_time_s=r["burn_time_s"], outcome_class=r["outcome_class"], outcome_basis=r["outcome_basis"],
                 quality_status=r["quality_status"], source_file=r["source_file"], source_row=r["source_row"], psi_url=psi_url("PSI-69"))
            for r in load("flex_droplet_tests")]


def cool_flame_tests():
    """CFI (PSI-39): droplet flame tests on the ISS with conditions only. Separate table: NASA recorded no outcome,
    so these never join droplet_extinction_tests (FLEX) or any outcome-based result."""
    return [dict(test_id=r["record_id"], fuel=r["fuel"], material_id=r["material_id"], test_date=r["test_date"],
                 pressure_kpa=r["pressure_kpa"], pressure_atm=r["pressure_atm"], o2_pct=r["o2_pct"], n2_pct=r["n2_pct"], he_pct=r["he_pct"],
                 diluent=("He" if (f(r["he_pct"]) or 0) > 0 else "N2 (air-like)"), fiber_supported=r["fiber_supported"],
                 outcome_class=r["outcome_class"], outcome_basis=r["outcome_basis"], quality_status=r["quality_status"],
                 source_file=r["source_file"], source_row=r["source_row"], psi_url=psi_url("PSI-39"))
            for r in load("cfi_cool_flame_tests")]


def gas_flame_tests():
    """ACME gaseous flames on the ISS (CFI-G with NASA outcome codes; Flame Design conditions only).
    A different experiment kind from solids and droplets: never mixed into those tables."""
    out = []
    for tbl, acc in (("acme_cfig_tests", "PSI-159"), ("acme_flame_design_tests", "PSI-10")):
        for r in load(tbl):
            out.append(dict(test_id=r["record_id"], investigation=r["investigation"], flame_type=r["flame_type"], fuel=r["fuel"],
                            material_id=r["material_id"], o2_pct=r["o2_pct"], o2_status=r["o2_status"], pressure_kpa=r["pressure_kpa"],
                            pressure_status=r["pressure_status"], outcome_class=r["outcome_class"], outcome_basis=r["outcome_basis"],
                            test_end_raw=r.get("test_end_raw", ""), burn_time_s=r.get("burn_time_s", ""), quality_status=r["quality_status"],
                            source_file=r["source_file"], source_row=r["source_row"], psi_url=psi_url(acc)))
    return out


def spice_conditions():
    return [dict(record_id=r["record_id"], fuel=r["fuel"], material_id=r["material_id"], nozzle_diameter_mm=r["nozzle_diameter_mm"],
                 fuel_rate_mg_s=r["fuel_rate_mg_s"], air_velocity_cm_s=r["air_velocity_cm_s"], gmt_day_of_year=r["gmt_day_of_year"],
                 source_file=r["source_file"], source_row=r["source_row"], psi_url=psi_url("PSI-107"))
            for r in load("spice_flames") if not r["duplicate_of"]]


def smoke_tests():
    out = []
    for r in load("same_smoke_tests"):
        out.append(dict(record_id=r["record_id"], investigation="SAME", material_id=r["material_id"], material=r["material_original_name"].split(":")[0],
                        flow_cm_s=r["flow_cm_s"], heater_resistance_ratio="", aging_time_s=(f(r["aging_duration_min"]) or 0) * 60 if r["aging_duration_min"] else "",
                        is_aged_measurement="", weight_loss_rate_mg_min=r["weight_loss_rate_mg_min"], source_file=r["source_file"], source_row=r["source_row"]))
    for r in load("same_r_smoke_tests"):
        out.append(dict(record_id=r["record_id"], investigation="SAME-R", material_id=r["material_id"], material=r["material_original_name"],
                        flow_cm_s=r["inlet_velocity_cm_s"], heater_resistance_ratio=r["heater_resistance_ratio"], aging_time_s=r["net_aging_time_s"],
                        is_aged_measurement=r["is_aged_measurement"], weight_loss_rate_mg_min="", source_file=r["source_file"], source_row=r["source_row"]))
    return out  # same measurement family (smoke generation by heating); columns not shared are left blank, never filled


def coverage(solids):
    """How many space tests exist near each mission design point (|O2| <= 2 points, |P| <= 15 kPa, same gravity)."""
    out = []
    for m, d in MISSIONS.items():
        near = [t for t in solids if f(t["o2_initial_pct"]) is not None and abs(f(t["o2_initial_pct"]) - d["o2_pct"]) <= 2
                and abs(f(t["pressure_kpa"]) - d["pressure_kpa"]) <= 15 and abs(t["gravity_g"] - d["gravity_g"]) < 0.01]
        out.append(dict(mission=m, gravity_g=d["gravity_g"], o2_pct=d["o2_pct"], pressure_kpa=d["pressure_kpa"],
                        space_solid_tests_near=len(near), space_tests_near_observed_outcome=sum(t["outcome_basis"] == "observed" for t in near),
                        rule="same gravity, O2 within 2 points, pressure within 15 kPa (pressure of space tests is assumed ISS cabin)"))
    return out


def powerbi(solids, droplets, spice, smoke, cov):
    silver_tables = {n: load(n) for n in ("bass2_tests", "bass_tests", "saffire1_tests", "saffire2_tests", "saffire3_tests",
                                          "same_smoke_tests", "same_r_smoke_tests", "flex_droplet_tests", "spice_flames",
                                          "cfi_cool_flame_tests", "flex2_test_matrix",
                                          "acme_cfig_tests", "acme_flame_design_tests", "acme_bre_sessions", "psi_session_logs")}
    by_inv = defaultdict(list)
    for rows in silver_tables.values():
        for r in rows: by_inv[r["investigation_id"]].append(r)
    inv = []
    for acc, m in INVESTIGATIONS.items():
        j = investigation_json(acc); rows = by_inv.get(acc, [])
        inv.append(dict(investigation_id=acc, acronym=m["acronym"], role=m["role"], experiment_kind=m["kind"], platform=m["platform"],
                        title=j.get("title", ""), doi=j.get("doi", ""), start_date=str(j.get("investigationStartDate", ""))[:10],
                        end_date=str(j.get("investigationEndDate", ""))[:10], records=len(rows),
                        records_with_warnings=sum(r["quality_status"] == "warning" for r in rows),
                        has_experimental_table=bool(m["table"]), psi_url=psi_url(acc)))
    mats = load("materials", "materials"); samples = load("material_samples", "materials"); props = load("material_properties", "materials")
    mo = []
    for mt in mats:
        s = [x for x in samples if x["material_id"] == mt["material_id"]]
        recs = {x["record_id"] for x in s}
        sol = [t for t in solids if t["test_id"] in recs]
        mo.append(dict(material_id=mt["material_id"], material=mt["material_normalized_name"], family=mt["material_family"],
                       candidate_family=mt["candidate_family"], classification_basis=mt["classification_basis"],
                       investigations=mt["investigations"], samples=len(s),
                       solid_flame_tests=len(sol), observed_outcomes=sum(t["outcome_basis"] == "observed" for t in sol),
                       burned=sum(t["outcome_class"] == "Burned" for t in sol),
                       went_out=sum(t["outcome_class"] in ("Extinction", "No Ignition", "Not Sustained", "Blowoff") for t in sol),
                       properties_available=", ".join(sorted({p["property"] for p in props if p["material_id"] == mt["material_id"]})),
                       properties_missing="density, mass, thermal properties, composition (not in NASA tables)"))
    outc = Counter((t["investigation"], t["outcome_class"], t["outcome_basis"]) for t in solids)
    outcomes = [dict(investigation=k[0], outcome_class=k[1], outcome_basis=k[2], tests=v) for k, v in sorted(outc.items())]
    dq = []
    for name, rows in silver_tables.items():
        dq.append(dict(table=name, records=len(rows), valid=sum(r["quality_status"] == "valid" for r in rows),
                       warnings=sum(r["quality_status"] == "warning" for r in rows),
                       pct_valid=round(100 * sum(r["quality_status"] == "valid" for r in rows) / max(1, len(rows)), 1)))
    flame = [t for t in solids]
    named = sum(t["material_identity"] == "named in NASA table" for t in flame)
    kpis = [
        ("solid_flame_tests_total", "count(gold/analytics/solid_fire_tests)", len(flame), "tests"),
        ("pct_tests_material_named", "named / total * 100", round(100 * named / len(flame), 1), "%"),
        ("pct_outcomes_observed", "outcome_basis=='observed' / total * 100", round(100 * sum(t["outcome_basis"] == "observed" for t in flame) / len(flame), 1), "%"),
        ("pct_outcomes_inferred", "outcome_basis=='inferred' / total * 100", round(100 * sum(t["outcome_basis"] == "inferred" for t in flame) / len(flame), 1), "%"),
        ("o2_tested_min_pct", "min(o2_initial_pct)", min(f(t["o2_initial_pct"]) for t in flame if f(t["o2_initial_pct"]) is not None), "%vol"),
        ("o2_tested_max_pct", "max(o2_initial_pct)", max(f(t["o2_initial_pct"]) for t in flame if f(t["o2_initial_pct"]) is not None), "%vol"),
        ("space_tests_at_moon_mars_design_point", "coverage.space_solid_tests_near for Lunar+Mars", sum(c["space_solid_tests_near"] for c in cov if c["mission"] in ("Lunar habitat", "Mars habitat")), "tests"),
        ("droplet_tests_total", "count(FLEX)", len(droplets), "tests"),
        ("droplet_pressure_range_kpa", "min-max(pressure_kpa) FLEX", f"{min(f(d['pressure_kpa']) for d in droplets if f(d['pressure_kpa'])):.1f}-{max(f(d['pressure_kpa']) for d in droplets if f(d['pressure_kpa'])):.1f}", "kPa"),
        ("smoke_records_total", "count(SAME + SAME-R)", len(smoke), "records"),
        ("spice_unique_flame_conditions", "count(SPICE excluding exact duplicates)", len(spice), "conditions"),
        ("materials_total", "count(materials)", len(mats), "materials"),
        ("materials_unknown_identity", "count(material_family=='Unknown')", sum(m["material_family"] == "Unknown" for m in mats), "materials"),
    ]
    kp = [dict(kpi=k, formula=fo, value=v, unit=u, refreshed_at=RUN_TS) for k, fo, v, u in kpis]
    return inv, mo, outcomes, dq, kp


def ml_table(solids):
    """Only observed labels; binary target burned vs did_not_continue. Grouped split by investigation+date to limit leakage."""
    rows = []
    for t in solids:
        if t["outcome_basis"] != "observed" or not t["o2_initial_pct"] or not t["flow_min_cm_s"]: continue
        if t["outcome_class"] not in ("Burned", "Extinction", "Blowoff", "No Ignition", "Not Sustained"): continue
        g = f"{t['investigation']}|{t['test_date']}"
        split = "test" if int(hashlib.md5(g.encode()).hexdigest(), 16) % 5 == 0 else "train"
        rows.append(dict(test_id=t["test_id"], o2_initial_pct=t["o2_initial_pct"], flow_min_cm_s=t["flow_min_cm_s"],
                         thickness_mm=t["thickness_mm"], diameter_mm=t["diameter_mm"], geometry=t["geometry"],
                         material_family_effective=t["material_family_effective"], material_identity=t["material_identity"],
                         target_burned=int(t["outcome_class"] == "Burned"), label_source="observed (NASA note)",
                         split=split, split_group=g, source_file=t["source_file"], source_row=t["source_row"]))
    return rows


def build():
    solids = solid_fire_tests(); droplets = droplet_tests(); spice = spice_conditions(); smoke = smoke_tests()
    cov = coverage(solids)
    write_csv(GOLD / "analytics" / "solid_fire_tests.csv", solids)
    write_csv(GOLD / "analytics" / "droplet_extinction_tests.csv", droplets)
    write_csv(GOLD / "analytics" / "cool_flame_tests.csv", cool_flame_tests())
    write_csv(GOLD / "analytics" / "gas_flame_tests.csv", gas_flame_tests())
    write_csv(GOLD / "analytics" / "gas_jet_flame_conditions.csv", spice)
    write_csv(GOLD / "analytics" / "smoke_generation_tests.csv", smoke)
    write_csv(GOLD / "analytics" / "mission_coverage.csv", cov)
    inv, mo, outcomes, dq, kp = powerbi(solids, droplets, spice, smoke, cov)
    write_csv(GOLD / "powerbi" / "investigation_overview.csv", inv)
    write_csv(GOLD / "powerbi" / "material_overview.csv", mo)
    write_csv(GOLD / "powerbi" / "outcome_summary.csv", outcomes)
    write_csv(GOLD / "powerbi" / "data_quality_overview.csv", dq)
    write_csv(GOLD / "powerbi" / "kpis.csv", kp)
    ml = ml_table(solids)
    write_csv(GOLD / "ml" / "solid_outcome_features.csv", ml)
    legacy(solids, inv)
    return dict(solids=solids, droplets=droplets, spice=spice, smoke=smoke, ml=ml, kpis=kp, coverage=cov)


def legacy(solids, inv):
    """Keep data/processed/ (used by the Kaggle notebook) regenerated from Gold, with the old column names."""
    old = []
    for t in solids:
        old.append(dict(test_id=t["test_id"], accession=t["investigation_id"], investigation=t["investigation"], platform=t["platform"],
                        gravity_g=0, material_raw=t["material_raw"], material_family=t["material_family_effective"], geometry=t["geometry"],
                        thickness_mm=t["thickness_mm"], o2_initial_pct=t["o2_initial_pct"], o2_final_pct=t["o2_final_pct"],
                        pressure_kpa=t["pressure_kpa"], pressure_assumed=True, flow_start_cm_s=t["flow_start_cm_s"],
                        flow_min_cm_s=t["flow_min_cm_s"], flow_direction=t["flow_direction"], outcome=t["outcome_class"],
                        outcome_basis=t["outcome_basis"], burn_time_s=t["burn_time_s"], ug_burn_length=t["ug_burn_length"],
                        one_g_burn_length=t["one_g_burn_length"], notes_raw=t["notes_raw"], psi_url=t["psi_url"], doi=t["doi"],
                        material_identity=t["material_identity"]))
    write_csv(PROCESSED / "solids_tests.csv", old)
    write_csv(PROCESSED / "investigations.csv", inv)


if __name__ == "__main__":
    out = build()
    for k, v in out.items(): print(k, len(v))
    for k in out["kpis"]: print(f"  {k['kpi']:40s} {k['value']} {k['unit']}")
