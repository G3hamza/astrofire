"""Demo script (docs/DEMO_SCRIPT.md), step by step, against the API the UI uses. PSI data only.
(UI rendering is checked by hand in the browser; see docs/DEMO_SCRIPT.md.)"""
from fastapi.testclient import TestClient
from backend.app import app

c = TestClient(app)
NOMEX = "Aramid fabric (Nomex)"


def kpi(name):
    return next(k["value"] for k in c.get("/api/analytics/overview").json()["kpis"] if k["kpi"] == name)


def test_step1_home_zero_tests_at_moon_mars():
    assert kpi("space_tests_at_moon_mars_design_point") == "0"
    assert int(kpi("solid_flame_tests_total")) > 200


def test_step2_iss_nomex_has_traceable_evidence():
    r = c.post("/api/scenario", json={"material": NOMEX, "mission": "iss"}).json()
    assert r["verdict"] != "Insufficient validated experimental evidence"
    assert len(r["evidence"]) >= 5
    for e in r["evidence"]:
        assert e["psi_url"].startswith("https://psi.nasa.gov/") and e["source_file"] and e["source_row"]


def test_step3_mars_nomex_insufficient_with_reasons_and_closest_flames():
    r = c.post("/api/scenario", json={"material": NOMEX, "mission": "mars"}).json()
    assert r["verdict"] == "Insufficient validated experimental evidence"
    assert r["blockers"] and {w["topic"] for w in r["why_untested"]} == {"gravity", "oxygen", "pressure"}
    gas = [a for a in r["atmosphere_evidence"] if a["kind"] == "gas flame"]
    assert gas and abs(gas[0]["o2_pct"] - 34) < 1 and gas[0]["psi_url"].startswith("https://psi.nasa.gov/")


def test_step4_gaps_moon_mars_have_no_psi_tests():
    cells = c.get("/api/gaps").json()
    pins = [x for x in cells if any(m.startswith(("Lunar", "Mars")) for m in x["mission_design_points"])]
    assert len(pins) == 2 and all(x["space_tests"] == 0 for x in pins)


def test_step5_experiments_show_every_psi_investigation():
    assert len(c.get("/api/investigations").json()) == 24
