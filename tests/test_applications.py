"""Phase 5: data for predictive modeling, equipment implications per pillar, Earth applications."""
import csv, io, json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import app

ROOT = Path(__file__).resolve().parents[1]
c = TestClient(app)
PROFILES = {p["investigation_id"]: p for p in json.loads((ROOT / "data/gold/analytics/investigation_profiles.json").read_text(encoding="utf-8"))}


def test_dataset_catalog_matches_files():
    cat = c.get("/api/datasets").json()
    names = {d["name"] for d in cat["datasets"]}
    assert {"ml_solid_outcomes", "solid_fire_tests", "droplet_extinction_tests", "smoke_generation_tests"} <= names
    for d in cat["datasets"]:
        with open(ROOT / d["file"], encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert d["rows"] == len(rows) and [x["name"] for x in d["columns"]] == list(rows[0].keys())
        assert d["caveats"]
    assert "not validated" in cat["ml_readme"].lower()


def test_dataset_download_and_whitelist():
    r = c.get("/api/datasets/solid_fire_tests.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert len(list(csv.DictReader(io.StringIO(r.text)))) == 263
    for bad in ("secret", "..%2F..%2F.env", "quarantine"):
        assert c.get(f"/api/datasets/{bad}.csv").status_code == 404


def test_equipment_quotes_are_nasa_text():
    pillars = {p["pillar"]: p for p in c.get("/api/equipment-insights").json()}
    assert set(pillars) == {"prevention", "detection", "suppression"}
    assert {"SAME", "SAME-R"} <= {i["acronym"] for i in pillars["detection"]["investigations"]}
    assert "FLEX" in {i["acronym"] for i in pillars["suppression"]["investigations"]}
    for p in pillars.values():
        assert "not a NASA result" in p["interpretation_label"]
        for i in p["investigations"]:
            prof = PROFILES[i["investigation_id"]]
            text = " ".join((prof["research_impacts"] + " " + prof["objective"]).split())
            assert all(" ".join(s.split()) in text for s in i["nasa_says"])          # quoted, not written by us


def test_earth_applications_sources():
    e = c.get("/api/earth-applications").json()
    assert {s["id"] for s in e["spinoffs"]} >= {"CR-spinoff-fire-detector", "CR-spinoff-air-tanks", "CR-spinoff-fire-attire", "CR-water-mist"}
    assert "does not validate" in e["caveat"]
    for i in e["from_psi_investigations"]:
        assert all(" ".join(s.split()) in " ".join(PROFILES[i["investigation_id"]]["research_impacts"].split()) for s in i["nasa_says"])
        assert not any("far from Earth" in s for s in i["nasa_says"])
