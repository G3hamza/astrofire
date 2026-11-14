"""Gate 2 frontend: served by FastAPI at "/", API routes untouched, honesty wording rules (NFR1)."""
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app import app, APP_DIST

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend-app" / "src"
c = TestClient(app)
built = pytest.mark.skipif(not (APP_DIST / "index.html").is_file(), reason="frontend-app not built (npm run build)")


@built
@pytest.mark.parametrize("path", ["/", "/style", "/scenario", "/compare", "/gaps", "/charts", "/experiments", "/materials", "/data"])
def test_spa_routes_serve_index(path):
    r = c.get(path)
    assert r.status_code == 200
    assert '<div id="root">' in r.text


@built
def test_favicon_served():
    assert c.get("/favicon.svg").status_code == 200


def test_api_routes_not_shadowed_by_spa():
    assert c.get("/api/stats").json()["tests"] > 0
    assert c.get("/docs").status_code == 200
    r = c.get("/api/does-not-exist")
    assert r.status_code == 404 and "detail" in r.json()


def test_no_probability_wording_in_ui():
    """NFR1: never 'probability', '% chance' or 'prediction' in UI copy. The only allowed mentions are
    negations ('not a probability' / 'NOT a calibrated probability')."""
    bad = []
    for f in SRC.rglob("*.ts*"):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            for m in re.finditer(r"probab|% ?chance|predict", low):
                if not re.search(r"not (a |a calibrated )?probab", low):
                    bad.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()}")
    assert not bad, "Forbidden wording:\n" + "\n".join(bad)


LITE = ROOT / "frontend"


def test_lite_backup_app_is_served():
    for path in ("/lite/", "/lite/app.js", "/lite/style.css"):
        assert c.get(path).status_code == 200, path
    assert "StarryNight Lite" in c.get("/lite/").text


def test_lite_has_no_probability_wording_and_no_external_scripts():
    for f in LITE.glob("*.*"):
        txt = f.read_text(encoding="utf-8").lower()
        for m in re.finditer(r"probab|% ?chance|predict", txt):
            line = txt[max(0, m.start() - 40): m.end() + 10]
            assert "not a probab" in line, f"{f.name}: {line}"
        assert "<script src=\"http" not in txt and "cdn" not in txt, f"{f.name} must work offline"


def test_lite_without_slash_redirects():
    r = c.get("/lite", follow_redirects=False)
    assert r.status_code in (301, 302, 307, 308) and r.headers["location"].endswith("/lite/")
