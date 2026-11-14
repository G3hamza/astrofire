"""Investigation profiles (challenge: summarize objectives, fuels, conditions, variables, sensors; compare investigations)."""
import csv, json
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import app
from pipelines.common import INVESTIGATIONS

ROOT = Path(__file__).resolve().parents[1]
c = TestClient(app)
PROFILES = json.loads((ROOT / "data/gold/analytics/investigation_profiles.json").read_text(encoding="utf-8"))
BY_ID = {p["investigation_id"]: p for p in PROFILES}


def test_one_profile_per_investigation():
    assert set(BY_ID) == set(INVESTIGATIONS)
    assert len(PROFILES) == len(INVESTIGATIONS) == 24


def test_nasa_text_matches_psi_metadata():
    """Objective text is copied from NASA's investigation.json, not written by us."""
    for acc, p in BY_ID.items():
        j = json.loads((ROOT / "data/raw/psi" / INVESTIGATIONS[acc]["folder"] / "investigation.json").read_text(encoding="utf-8"))
        assert p["objective"][:60] == " ".join(j["objective"].split())[:60]
        assert p["field_basis"]["objective"] == "nasa_text"


def test_curation_has_basis_and_valid_values():
    for p in PROFILES:
        assert p["pillar"] in ("prevention", "detection", "suppression", "fundamental")
        assert p["relevance_tier"] in ("direct", "related", "background")
        assert len(p["curation_basis"]) > 30


def test_challenge_named_investigations_are_direct():
    """The challenge names BASS, BASS-II, Saffire I-III (flammability), SAME, SAME-R (detection), FLEX (suppression)."""
    direct = {p["acronym"] for p in PROFILES if p["relevance_tier"] == "direct"}
    assert direct == {"BASS", "BASS-II", "SAFFIRE-I", "SAFFIRE-II", "SAFFIRE-III", "SAME", "SAME-R", "FLEX"}
    assert BY_ID["PSI-69"]["pillar"] == "suppression"
    assert {BY_ID["PSI-102"]["pillar"], BY_ID["PSI-101"]["pillar"]} == {"detection"}


def test_challenge_hardware_groups():
    hw = lambda a: BY_ID[a]["hardware_family"]
    assert len({hw(a) for a in ("PSI-25", "PSI-26", "PSI-107", "PSI-106")}) == 1          # MSG flow duct
    assert len({hw(a) for a in ("PSI-69", "PSI-68", "PSI-39")}) == 1                      # CIR + MDCA
    assert len({hw(a) for a in ("PSI-10", "PSI-20", "PSI-21", "PSI-22", "PSI-23", "PSI-159")}) == 1  # ACME (6 experiments)


def test_e_field_marked_as_partial_gravity_mimic_only():
    note = BY_ID["PSI-22"]["partial_gravity_note"]
    assert note and "mimic" in note.lower() and "not a partial-gravity test" in note.lower()


def test_conditions_computed_from_tables():
    """BASS-II: pressure is constant (assumed ISS cabin) and oxygen varied; ranges match the Gold table."""
    p = BY_ID["PSI-25"]
    assert "Oxygen (initial)" in p["varied_factors"]
    assert any(c["factor"] == "Pressure" for c in p["constant_factors"])
    o2 = next(c for c in p["conditions"] if c["factor"] == "Oxygen (initial)")
    vals = [float(r["o2_initial_pct"]) for r in csv.DictReader(open(ROOT / "data/gold/analytics/solid_fire_tests.csv", encoding="utf-8"))
            if r["investigation_id"] == "PSI-25" and r["o2_initial_pct"]]
    assert (o2["min"], o2["max"]) == (min(vals), max(vals))


def test_sensor_matches_carry_evidence():
    for p in PROFILES:
        for s in p["sensors"] + p["measured_quantities"]:
            assert s["evidence"]


def test_api_profiles_and_filters():
    assert len(c.get("/api/investigations/profiles").json()) == 24
    det = c.get("/api/investigations/profiles?pillar=detection").json()
    assert {"SAME", "SAME-R", "DAFT"} <= {p["acronym"] for p in det}
    assert c.get("/api/investigations/profiles?pillar=bogus").status_code == 422
    assert c.get("/api/investigations/profiles?tier=nope").status_code == 422
    assert c.get("/api/investigations/psi-25/profile").json()["acronym"] == "BASS-II"
    assert c.get("/api/investigations/PSI-999/profile").status_code == 404


def test_api_compare():
    r = c.get("/api/investigations/compare?ids=PSI-25,PSI-26").json()
    assert r["same"]["hardware_family"] and r["same"]["pillar"]
    assert "Pressure" in r["factors"]["in_all"]
    # NASA's BASS table records no oxygen value, so oxygen is a BASS-II-only factor (a real difference, shown to users)
    assert "Oxygen (initial)" in r["factors"]["only_in"]["PSI-25"]
    assert "Oxygen (initial)" in BY_ID["PSI-26"]["not_recorded_factors"]
    r2 = c.get("/api/investigations/compare?ids=PSI-25,PSI-69").json()
    assert not r2["same"]["fuel_phase"]
    assert c.get("/api/investigations/compare?ids=PSI-25").status_code == 422
    assert c.get("/api/investigations/compare?ids=PSI-25,PSI-25").status_code == 422
    assert c.get("/api/investigations/compare?ids=PSI-25,PSI-0").status_code == 404


def test_api_hardware_groups():
    g = c.get("/api/hardware-groups").json()
    assert sum(len(x["investigations"]) for x in g) == 24
    acme = next(x for x in g if x["hardware_family"].startswith("CIR + ACME"))
    assert len(acme["investigations"]) == 6
