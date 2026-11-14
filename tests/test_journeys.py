"""Phase 6: complete user journeys (every API call a screen makes, in order), input limits, error handling, security."""
import csv, io, json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai import api as A, config
from backend.app import app

ROOT = Path(__file__).resolve().parents[1]
c = TestClient(app)
NOMEX = "Aramid fabric (Nomex)"
SCREENS = ["/", "/scenario", "/compare", "/gaps", "/charts", "/experiments", "/investigations", "/rank", "/ask", "/applications",
           "/materials", "/data", "/about", "/style"]


@pytest.fixture(autouse=True)
def template_mode():
    config.set_llm("none"); A._hits.clear(); A._cache.clear()
    yield
    config.set_llm(None)


def test_every_screen_serves_the_app():
    if not (ROOT / "frontend-app/dist/index.html").exists():
        pytest.skip("frontend not built")
    for s in SCREENS:
        r = c.get(s)
        assert r.status_code == 200 and '<div id="root">' in r.text, s
    assert c.get("/lite/").status_code == 200
    assert c.get("/api/not-a-route").status_code == 404


def test_journey_demo_script():
    """docs/DEMO_SCRIPT.md steps 1-6, through the same endpoints the screens call."""
    st = c.get("/api/stats").json()
    assert st["tests"] == 263 and st["o2_range_tested"] == [13.6, 22.2]                      # 1 Home
    iss = c.post("/api/scenario", json={"material": NOMEX, "mission": "iss"}).json()
    assert iss["verdict"] == "Borderline in tested evidence" and len(iss["evidence"]) == 5   # 2 Nomex ISS
    mars = c.post("/api/scenario", json={"material": NOMEX, "mission": "mars"}).json()
    assert mars["verdict"] == "Insufficient validated experimental evidence" and len(mars["blockers"]) == 3   # 3 Mars
    assert mars["gravity_bounds"] and not mars["gravity_bounds"]["bounds_cover_request"]
    cols = [c.post("/api/scenario", json={"material": NOMEX, "mission": m}).json()["verdict"] for m in ("iss", "exploration", "moon", "mars")]
    assert cols[0] != cols[-1]                                                                # 4 Compare
    cells = c.get("/api/gaps").json()
    assert sum(1 for x in cells if x["space_tests"]) >= 1 and any(x["mission_design_points"] for x in cells)   # 5 Gaps
    assert len(c.get("/api/investigations").json()) == 24                                     # 6 Experiments


def test_journey_researcher():
    """Rank for a habitat -> open the top investigation -> compare two -> ask the analyst -> download its data."""
    top = c.get("/api/rank?habitat=moon").json()["ranked"][0]
    prof = c.get(f"/api/investigations/{top['investigation_id']}/profile").json()
    assert prof["acronym"] == top["acronym"] and prof["objective"]
    cmp_ = c.get(f"/api/investigations/compare?ids={top['investigation_id']},PSI-25").json()
    assert cmp_["factors"]["in_all"] is not None
    ans = c.post("/api/ask", json={"question": f"Summarize {top['acronym']}", "habitat": "moon"}).json()
    assert ans["findings"] and ans["mode"] == "template"
    follow = c.post("/api/ask", json={"question": "What did it vary between tests?", "habitat": "moon",
                                      "history": [{"role": "user", "content": f"Summarize {top['acronym']}"},
                                                  {"role": "assistant", "content": ans["answer"]}]}).json()
    assert follow["intent"] == "summary"
    d = c.get("/api/datasets/droplet_extinction_tests.csv")
    assert d.status_code == 200 and len(list(csv.DictReader(io.StringIO(d.text)))) == 274


def test_journey_free_text_scenario():
    p = c.post("/api/scenario/parse", json={"text": "Nomex on Mars at 34% oxygen and 8.2 psi"}).json()
    assert p["scenario"]["material"] == NOMEX and abs(p["scenario"]["pressure_kpa"] - 56.5) < 0.2
    r = c.post("/api/scenario", json=p["scenario"]).json()
    assert r["verdict"] == "Insufficient validated experimental evidence"


@pytest.mark.parametrize("body", [{"o2_pct": 150}, {"o2_pct": -1}, {"gravity_g": 3}, {"pressure_kpa": 0}, {"flow_cm_s": 999},
                                  {"mission": "venus"}, {"material": ""}, {"material": "   "}, {"material": "x" * 200}])
def test_scenario_rejects_impossible_inputs(body):
    assert c.post("/api/scenario", json={"material": NOMEX, **body}).status_code == 422


@pytest.mark.parametrize("url", ["/api/experiments?investigation_id=PSI-25&limit=0", "/api/experiments?investigation_id=PSI-25&limit=999999",
                                 "/api/experiments?investigation_id=PSI-25&offset=-1", "/api/measurements?quantity=o2&limit=0",
                                 "/api/map?material=" + "x" * 200, "/api/investigations/compare?ids=" + ",".join(["PSI-25"] * 60)])
def test_query_limits(url):
    assert c.get(url).status_code == 422


def test_free_text_limit():
    assert c.post("/api/scenario/parse", json={"text": "x" * 2000}).status_code == 422
    assert c.post("/api/scenario/parse", json={"text": ""}).status_code == 422


def test_unexpected_error_is_clean_json(monkeypatch):
    import backend.app as B
    monkeypatch.setattr(B.E, "gaps", lambda: 1 / 0)
    r = TestClient(app, raise_server_exceptions=False).get("/api/gaps")
    assert r.status_code == 500 and r.json()["request_id"] and "Traceback" not in r.text and "ZeroDivision" not in r.text


def test_security_headers_and_cors():
    r = c.get("/api/stats", headers={"Origin": "https://example.org"})
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["referrer-policy"] == "no-referrer"
    assert r.headers.get("access-control-allow-origin") == "*"


def test_no_secrets_in_responses_or_repo(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_SHOULD_NEVER_APPEAR_123456789")
    config.set_llm(None)
    for path in ("/api/ask/status", "/ai/health", "/api/stats"):
        assert "gsk_SHOULD" not in c.get(path).text
    assert (ROOT / ".gitignore").read_text().count(".env") >= 1
    assert ".env" in (ROOT / ".dockerignore").read_text()


def test_rate_limit_is_per_visitor_behind_proxy():
    A._hits.clear()
    for i in range(A.RATE):
        assert c.post("/ai/ask", json={"question": f"FLEX {i}"}, headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert c.post("/ai/ask", json={"question": "FLEX x"}, headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 429
    assert c.post("/ai/ask", json={"question": "FLEX y"}, headers={"X-Forwarded-For": "2.2.2.2, 10.0.0.1"}).status_code == 200
