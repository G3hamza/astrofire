"""'Why untested' explanations, atmosphere evidence (FLEX, CFI, ACME), free-text parsing, PSI coverage. PSI data only."""
import csv
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import app
from backend.scenario_parse import parse

ROOT = Path(__file__).resolve().parents[1]
c = TestClient(app)
NOMEX = "Aramid fabric (Nomex)"


def test_why_untested_matches_the_conditions():
    topics = lambda m: {w["topic"] for w in c.post("/api/scenario", json={"material": NOMEX, "mission": m}).json()["why_untested"]}
    assert topics("iss") == set()
    assert topics("exploration") == {"oxygen", "pressure"}
    assert topics("mars") == {"gravity", "oxygen", "pressure"}


def test_parse_reads_units_and_presets():
    r = parse("Nomex on Mars at 34% oxygen and 8.2 psi")["scenario"]
    assert r["material"] == NOMEX and r["mission"] == "mars" and r["pressure_kpa"] == 56.5
    r = parse("Acrylic window in a lunar habitat, 30% O2, 0.5 atm, 2 cm/s air flow")["scenario"]
    assert r["mission"] is None and r["gravity_g"] == 0.166 and r["o2_pct"] == 30 and r["pressure_kpa"] == 50.7 and r["flow_cm_s"] == 2


def test_parse_is_honest_about_unknown_material_and_defaults():
    out = parse("Kevlar seat cover in microgravity at 26% oxygen, 70 kPa")
    assert out["scenario"]["material"] == "Kevlar" and out["warnings"]
    assert {d["field"] for d in parse("Nomex on the ISS")["defaulted"]} == {"gravity_g", "o2_pct", "pressure_kpa", "flow_cm_s"}
    assert parse("hello")["warnings"]


def test_parse_endpoint_then_scenario_round_trip():
    p = c.post("/api/scenario/parse", json={"text": "PMMA in orbit at 31% oxygen and 54 kPa"}).json()
    r = c.post("/api/scenario", json=p["scenario"]).json()
    gas = [a for a in r["atmosphere_evidence"] if a["kind"] == "gas flame"]
    assert r["scenario"]["o2_pct"] == 31 and r["scenario"]["pressure_kpa"] == 54 and gas


def test_flex_atmosphere_evidence_is_separate_and_close():
    r = c.post("/api/scenario", json={"material": NOMEX, "mission": "exploration"}).json()
    drops = [a for a in r["atmosphere_evidence"] if a["kind"] == "droplet flame"]
    gas = [a for a in r["atmosphere_evidence"] if a["kind"] == "gas flame"]
    assert drops and all(a["test_id"].startswith(("FLEX-", "CFI-")) and a["diluent"].startswith("N2") for a in drops)
    assert drops[0]["o2_pct"] == 34.0 and drops[0]["pressure_kpa"] < 80
    assert gas and gas[0]["investigation"].startswith("ACME") and abs(gas[0]["o2_pct"] - 34) < 1 and gas[0]["pressure_kpa"] < 60
    assert not any(e["test_id"].startswith(("FLEX-", "CFIG-", "FD-")) for e in r["evidence"]), "flames must never count as material evidence"
    assert r["verdict"] == "Insufficient validated experimental evidence"


def test_other_experiment_endpoints():
    assert len(c.get("/api/droplets").json()) == 274
    assert len(c.get("/api/smoke").json()) == 117
    assert all(x["material_id"] == "MAT-kapton" for x in c.get("/api/smoke", params={"material_id": "MAT-kapton"}).json())
    assert len(c.get("/api/gas-jets").json()) == 435


def test_droplets_only_counted_in_orbit_cells():
    cells = c.get("/api/gaps").json()
    assert all(x["droplet_tests"] == 0 for x in cells if x["gravity_g"] != 0.0)
    assert sum(x["droplet_tests"] for x in cells) > 0


def test_cfi_loaded_once_without_invented_outcomes():
    rows = c.get("/api/cool-flames").json()
    assert len(rows) == 79 and len({r["test_id"] for r in rows}) == 79
    assert all(r["outcome_basis"] == "not_recorded" and r["outcome_class"] == "Unknown" for r in rows)
    q = list(csv.DictReader(open(ROOT / "data/quarantine/quarantine.csv", encoding="utf-8")))
    assert sum(1 for r in q if r["investigation"] == "CFI" and r["validation_rule"] == "duplicate:exact_row") == 8


def test_flex2_is_a_matrix_not_tests():
    m = c.get("/api/experiments", params={"investigation_id": "PSI-68"}).json()
    assert m["total"] == 8 and all(r["row_type"].startswith("test matrix") for r in m["records"])
    assert not any(r["test_id"].startswith("FLEX2") for r in c.get("/api/droplets").json() + c.get("/api/cool-flames").json())


def test_cfi_is_low_pressure_atmosphere_evidence():
    r = c.post("/api/scenario", json={"material": NOMEX, "gravity_g": 0, "o2_pct": 21, "pressure_kpa": 50, "flow_cm_s": 5}).json()
    cfi = [a for a in r["atmosphere_evidence"] if a["investigation"] == "CFI"]
    assert cfi and cfi[0]["pressure_kpa"] == 50.7 and cfi[0]["outcome_basis"] == "not_recorded"
    assert not any(e["test_id"].startswith("CFI-") for e in r["evidence"])


def test_all_24_psi_combustion_investigations_in_pipeline():
    inv = c.get("/api/investigations").json()
    assert len(inv) == 24
    for acc in ("PSI-10", "PSI-20", "PSI-159", "PSI-21", "PSI-22", "PSI-23", "PSI-106", "PSI-142", "PSI-47"):
        assert any(i["investigation_id"] == acc and int(i["records"]) > 0 for i in inv), acc


def test_acme_outcomes_only_from_nasa_codes():
    rows = c.get("/api/gas-flames").json()
    cfig = [r for r in rows if r["investigation"] == "ACME CFI-G"]
    assert len(cfig) == 333 and len([r for r in rows if r["investigation"] == "ACME Flame Design"]) == 327
    for r in cfig:
        if r["outcome_class"] == "Extinction": assert r["test_end_raw"] == "SE"
        if r["outcome_class"] == "Burned": assert r["test_end_raw"] == "FT"
    assert all(r["outcome_basis"] == "not_recorded" for r in rows if r["investigation"] == "ACME Flame Design")


def test_session_logs_are_never_tests():
    logs = c.get("/api/session-logs").json()
    assert len(logs) == 18 + 104 and all(not r["record_id"].startswith(("CFIG", "FD-")) for r in logs)
    q = list(csv.DictReader(open(ROOT / "data/quarantine/quarantine.csv", encoding="utf-8")))
    assert any(r["investigation"] == "ACME BRE" and r["validation_rule"] == "format:o2_percent_typo" for r in q)


def test_no_ntrs_paper_features_in_scenario():
    r = c.post("/api/scenario", json={"material": NOMEX, "mission": "moon"}).json()
    assert "reference_partial_gravity" not in r and "supporting_evidence" not in r
    for w in r["why_untested"]:
        assert w["source_url"].startswith("https://psi.nasa.gov/"), w
