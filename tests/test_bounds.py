"""Partial gravity (challenge): no PSI partial-gravity data; microgravity and normal-gravity results can only bound it."""
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import app

ROOT = Path(__file__).resolve().parents[1]
c = TestClient(app)
scen = lambda m, g, o, p: c.post("/api/scenario", json={"material": m, "gravity_g": g, "o2_pct": o, "pressure_kpa": p, "flow_cm_s": 5}).json()


def test_no_bounds_at_zero_g():
    assert scen("PMMA (acrylic)", 0.0, 21, 101.3)["gravity_bounds"] is None


def test_sibal_bracketed_at_cabin_air_with_nasa_1g_comparison():
    b = scen("Cotton-fiberglass (SIBAL)", 0.166, 21.5, 101.3)["gravity_bounds"]
    assert b["bounds_cover_request"] and b["lower_bound"]["tests"] > 0
    assert b["upper_bound"]["pairs"] and all(p["test_id"].startswith("SAFFIRE-II") for p in b["upper_bound"]["pairs"])
    assert "still untested" in b["applies"]                  # bracketing is not a value for 0.166 g


def test_habitat_atmosphere_not_bounded():
    r = scen("Aramid fabric (Nomex)", 0.166, 34, 56.5)
    b = r["gravity_bounds"]
    assert not b["bounds_cover_request"] and "Insufficient validated experimental evidence" in b["applies"]
    assert r["verdict"] == "Insufficient validated experimental evidence"


def test_material_without_1g_data_says_so():
    b = scen("Polyetherimide (Ultem)", 0.38, 21, 101.3)["gravity_bounds"]
    assert b["upper_bound"]["pairs"] == [] and "no 1 g result" in b["upper_bound"]["note"]


def test_e_field_is_mimic_and_luci_fm2_are_future():
    b = scen("PMMA (acrylic)", 0.38, 21, 101.3)["gravity_bounds"]
    assert "mimic" in b["partial_gravity_mimic"]["text"] and "PSI-22" in b["partial_gravity_mimic"]["url"]
    assert {x["name"].split()[0] for x in b["coming_next"]} == {"LUCI", "FM2"}


def test_bound_rows_traceable():
    for p in scen("PMMA (acrylic)", 0.38, 22, 101.3)["gravity_bounds"]["upper_bound"]["pairs"]:
        assert (ROOT / p["source_file"]).exists() and int(p["source_row"]) > 0


def test_ntrs_paper_tables_removed():
    for p in ("data/gold/analytics/partial_gravity_limits.csv", "data/gold/analytics/literature_fire_tests.csv",
              "data/silver/reference/partial_gravity_limits.csv"):
        assert not (ROOT / p).exists(), p
