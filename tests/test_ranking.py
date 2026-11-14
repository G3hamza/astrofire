"""Habitat relevance ranking (challenge: identify investigations most relevant to spacecraft, stations, Moon/Mars bases, rovers)."""
from fastapi.testclient import TestClient
from backend.app import app
from backend.engine import MISSIONS
from backend.ranking import RANK_WEIGHTS
from pipelines.common import HABITATS

c = TestClient(app)


def test_habitats_cover_challenge_environments_and_range():
    kinds = {h["kind"] for h in c.get("/api/habitats").json().values()}
    assert {"spacecraft", "space station", "lunar surface base", "Martian surface base", "pressurized rover"} <= kinds
    for k in ("moon", "rover", "mars"):  # challenge: O2 "30% or greater" at "10.2 psi or less" (70.3 kPa)
        assert HABITATS[k]["o2_pct"] >= 30 and HABITATS[k]["pressure_kpa"] <= 70.3


def test_single_definition_of_missions():
    for k, m in MISSIONS.items():
        assert (m["o2_pct"], m["pressure_kpa"], m["gravity_g"]) == (HABITATS[k]["o2_pct"], HABITATS[k]["pressure_kpa"], HABITATS[k]["gravity_g"])
    assert list(c.get("/api/missions").json()) == ["iss", "exploration", "moon", "mars"]  # existing UI pickers unchanged


def test_rank_shape_and_explanations():
    r = c.get("/api/rank?habitat=moon").json()
    assert r["weights"] == RANK_WEIGHTS and sum(RANK_WEIGHTS.values()) == 100
    assert len(r["ranked"]) == 24 and [x["rank"] for x in r["ranked"]] == list(range(1, 25))
    scores = [x["score"] for x in r["ranked"]]
    assert scores == sorted(scores, reverse=True) and all(0 <= s <= 100 for s in scores)
    for x in r["ranked"]:
        assert set(x["components"]) == set(RANK_WEIGHTS) and len(x["reasons"]) >= 4
        assert abs(sum(RANK_WEIGHTS[k] * v for k, v in x["components"].items()) - x["score"]) < 0.2
    assert "not a probability" in r["caveat"]


def test_iss_top_is_solid_flammability_moon_says_gravity_is_only_bounded():
    iss = c.get("/api/rank?habitat=iss").json()["ranked"]
    assert all(x["fuel_phase"] == "solid" for x in iss[:3])
    moon = c.get("/api/rank?habitat=moon").json()["ranked"]
    for x in moon:
        assert any("bound" in s for s in x["reasons"]) or x["condition_parts"]["gravity"] < 1
        assert x["condition_parts"]["gravity"] <= 0.5        # no PSI test at lunar gravity
    # BASS-II at assumed cabin pressure is far from 56.5 kPa: pressure part must be low and the reason must say "assumed"
    b2 = next(x for x in moon if x["acronym"] == "BASS-II")
    assert b2["condition_parts"]["pressure"] < 0.2 and any("assumed" in s for s in b2["reasons"])


def test_high_oxygen_investigations_rise_for_habitat_atmosphere():
    moon = {x["acronym"]: x["rank"] for x in c.get("/api/rank?habitat=moon").json()["ranked"]}
    iss = {x["acronym"]: x["rank"] for x in c.get("/api/rank?habitat=iss").json()["ranked"]}
    assert moon["ACME CFI-G"] <= 3 and moon["ACME CFI-G"] < iss["ACME CFI-G"]


def test_e_field_reason_mentions_mimic():
    ef = next(x for x in c.get("/api/rank?habitat=mars").json()["ranked"] if x["acronym"] == "ACME E-FIELD")
    assert any("mimic" in s.lower() for s in ef["reasons"])


def test_pillar_filter_and_custom_and_errors():
    det = c.get("/api/rank?habitat=iss&pillar=detection").json()["ranked"]
    assert det and all("detection" in (x["pillar"], x["pillar_secondary"]) for x in det)
    cu = c.get("/api/rank?habitat=custom&gravity_g=0&o2_pct=30&pressure_kpa=70").json()
    assert cu["habitat"]["o2_pct"] == 30 and len(cu["ranked"]) == 24
    assert c.get("/api/rank?habitat=custom&o2_pct=30").status_code == 422
    assert c.get("/api/rank?habitat=venus").status_code == 404
    assert c.get("/api/rank?habitat=moon&pillar=x").status_code == 422
    assert c.get("/api/rank?habitat=custom&gravity_g=0&o2_pct=150&pressure_kpa=70").status_code == 422
