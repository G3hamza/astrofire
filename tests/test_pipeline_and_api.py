"""Run after the pipeline:  python -m pipelines.orchestration.run_all && pytest -q"""
import csv, json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import app

ROOT = Path(__file__).resolve().parents[1]
c = TestClient(app)


def rows(p):
    return list(csv.DictReader(open(ROOT / "data" / p, encoding="utf-8")))


def test_no_shape_only_pmma():
    for r in rows("silver/materials/materials.csv"):
        if r["material_family"] == "PMMA (acrylic)":
            assert r["classification_basis"] == "explicit_name"


def test_inferred_never_reliable():
    for r in rows("gold/analytics/solid_fire_tests.csv"):
        if r["outcome_basis"] != "observed":
            assert r["label_reliable"] == "False"


def test_every_gold_row_traceable():
    for r in rows("gold/analytics/solid_fire_tests.csv"):
        assert r["source_file"] and r["source_row"]
        assert (ROOT / r["source_file"]).exists()


def test_moon_returns_insufficient_evidence():
    r = c.post("/api/scenario", json={"material": "Aramid fabric (Nomex)", "mission": "moon", "flow_cm_s": 5}).json()
    assert r["verdict"] == "Insufficient validated experimental evidence"
    assert any(w["topic"] == "gravity" for w in r["why_untested"]), "Moon scenario must explain the gravity gap"
    assert "NOT a calibrated probability" in r["nearby_burn_share_note"]


def test_iss_scenario_has_evidence_with_provenance():
    r = c.post("/api/scenario", json={"material": "PMMA (acrylic)", "mission": "iss", "flow_cm_s": 5}).json()
    assert r["evidence"] and all(e["source_file"] for e in r["evidence"])


def test_endpoints():
    for u in ["/api/stats", "/api/investigations", "/api/materials", "/api/material-families", "/api/materials/MAT-pmma",
              "/api/experiments?investigation_id=PSI-69&limit=3", "/api/measurements?record_id=FLEX-1", "/api/analytics/overview",
              "/api/data-quality", "/api/gaps", "/api/map", "/api/droplets", "/api/cool-flames", "/api/gas-flames", "/api/session-logs"]:
        assert c.get(u).status_code == 200, u
    for removed in ("/api/search?q=x", "/api/partial-gravity", "/api/literature-tests"):  # NTRS-based, not in challenge data
        assert c.get(removed).status_code == 404, removed
    assert c.get("/api/materials/MAT-nope").status_code == 404
    assert c.get("/api/experiments?investigation_id=PSI-62").status_code == 404
