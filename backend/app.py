"""AstroFire API.  Run:  uvicorn backend.app:app --reload   (from the project root)

Data: only NASA's PSI combustion repository (the Space Apps 2026 challenge resources). No API key needed.
"""
import csv, os, re
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi import Path as Path_
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .engine import Engine, MISSIONS

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app):
    """Warm the AI layer (BM25 index + 'what burned' summaries). No network calls."""
    from ai.api import warmup
    warmup()
    yield


app = FastAPI(title="AstroFire API", version="0.3", lifespan=lifespan)
# Read-only public data API: any origin may read it; only GET/POST are used.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["content-type", "x-api-key"])

import logging, uuid  # noqa: E402
from fastapi import Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

log = logging.getLogger("astrofire")
SECURITY_HEADERS = {"X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "X-Frame-Options": "SAMEORIGIN",
                    "Permissions-Policy": "camera=(), microphone=(), geolocation=()"}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    return response


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    """Never return a stack trace: log it, give the client a short id to report."""
    rid = uuid.uuid4().hex[:12]
    log.exception("Unhandled error %s on %s %s", rid, request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal error. The data endpoints and the template answers still work.",
                                                  "request_id": rid})


E = Engine()
DATA = Path(__file__).resolve().parents[1] / "data"

# AI layer (ai/): /api/ask, /api/ask/status, /ai/*. Registered before the SPA catch-all at the bottom of this file.
from ai.api import router as ai_router  # noqa: E402
app.include_router(ai_router)
SILVER_TABLES = {"PSI-25": "bass2_tests", "PSI-26": "bass_tests", "PSI-98": "saffire1_tests", "PSI-99": "saffire2_tests",
                 "PSI-100": "saffire3_tests", "PSI-102": "same_smoke_tests", "PSI-101": "same_r_smoke_tests",
                 "PSI-69": "flex_droplet_tests", "PSI-107": "spice_flames", "PSI-39": "cfi_cool_flame_tests",
                 "PSI-68": "flex2_test_matrix", "PSI-159": "acme_cfig_tests", "PSI-10": "acme_flame_design_tests",
                 "PSI-20": "acme_bre_sessions", **{a: "psi_session_logs" for a in ("PSI-21", "PSI-22", "PSI-23", "PSI-106", "PSI-142", "PSI-47")}}


def _rows(rel):
    with open(DATA / rel, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _clean(r):
    return {k: (None if v == "" else v) for k, v in r.items() if k != "source_record"}


from pydantic import Field, field_validator  # noqa: E402


class Scenario(BaseModel):
    """Physically meaningful ranges only (422 otherwise). Same defaults as before."""
    material: str = Field("PMMA (acrylic)", min_length=1, max_length=80)
    mission: str | None = Field(None, max_length=20)
    gravity_g: float = Field(0.0, ge=0, le=1.5)
    o2_pct: float = Field(21.0, ge=0, le=100)
    pressure_kpa: float = Field(101.3, ge=1, le=600)
    flow_cm_s: float = Field(5.0, ge=0, le=200)

    @field_validator("mission")
    @classmethod
    def known_mission(cls, v):
        if v is not None and v not in MISSIONS:
            raise ValueError(f"mission must be one of {sorted(MISSIONS)} or null")
        return v

    @field_validator("material")
    @classmethod
    def strip_material(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("material must not be empty")
        return v


@app.get("/api/stats")
def stats():
    return E.stats()


@app.get("/api/missions")
def missions():
    return MISSIONS


@app.get("/api/investigations")
def investigations():
    """All in-scope NASA investigations with record counts, dates, DOI and PSI link (Gold)."""
    return _rows("gold/powerbi/investigation_overview.csv")


def _profiles():
    """Investigation profiles (Gold, built by pipelines/transformation/profiles.py). Read once, then cached."""
    if not hasattr(_profiles, "cache"):
        p = DATA / "gold" / "analytics" / "investigation_profiles.json"
        if not p.is_file():
            raise HTTPException(503, "Investigation profiles not built. Run: python -m pipelines.orchestration.run_all")
        import json
        _profiles.cache = {x["investigation_id"]: x for x in json.loads(p.read_text(encoding="utf-8"))}
    return _profiles.cache


PILLAR_VALUES = ("prevention", "detection", "suppression", "fundamental")
TIER_VALUES = ("direct", "related", "background")


@app.get("/api/investigations/profiles")
def investigation_profiles(pillar: str | None = Query(None, description="prevention | detection | suppression | fundamental"),
                           tier: str | None = Query(None, description="direct | related | background")):
    """One profile per PSI investigation: NASA objective/hypothesis/approach/impacts, conditions, what varied vs stayed
    the same, sensors, data files, plus the team's pillar / relevance tier / hardware family (each with its basis)."""
    if pillar and pillar not in PILLAR_VALUES:
        raise HTTPException(422, f"pillar must be one of {PILLAR_VALUES}")
    if tier and tier not in TIER_VALUES:
        raise HTTPException(422, f"tier must be one of {TIER_VALUES}")
    return [p for p in _profiles().values()
            if (not pillar or pillar in (p["pillar"], p["pillar_secondary"])) and (not tier or p["relevance_tier"] == tier)]


@app.get("/api/investigations/compare")
def investigations_compare(ids: str = Query(..., max_length=200, description="2 to 6 comma-separated ids, e.g. PSI-25,PSI-69")):
    """Similarities and differences between investigations: shared vs unique factors, sensors, hardware, fuels."""
    want = list(dict.fromkeys(i.strip().upper() for i in ids.split(",") if i.strip()))
    if not 2 <= len(want) <= 6:
        raise HTTPException(422, "Give 2 to 6 distinct investigation ids.")
    P = _profiles()
    unknown = [i for i in want if i not in P]
    if unknown:
        raise HTTPException(404, f"Unknown investigation id(s): {unknown}. See /api/investigations/profiles.")
    from .compare import compare_profiles
    return compare_profiles([P[i] for i in want])


@app.get("/api/hardware-groups")
def hardware_groups():
    """Investigations grouped by shared hardware (CIR + ACME, CIR + MDCA, MSG flow duct, Saffire in Cygnus ...)."""
    from collections import defaultdict
    g = defaultdict(list)
    for p in _profiles().values():
        g[p["hardware_family"]].append({"investigation_id": p["investigation_id"], "acronym": p["acronym"], "pillar": p["pillar"],
                                        "relevance_tier": p["relevance_tier"], "fuel_phase": p["fuel_phase"]})
    return [{"hardware_family": k, "investigations": v} for k, v in sorted(g.items(), key=lambda kv: -len(kv[1]))]


@app.get("/api/habitats")
def habitats():
    """Crew habitat design points (spacecraft, ISS, Moon base, pressurized rover, Mars base). Single source: pipelines/common.HABITATS."""
    from pipelines.common import HABITATS
    return {k: {kk: v for kk, v in h.items() if kk != "in_missions"} for k, h in HABITATS.items()}


@app.get("/api/rank")
def rank_investigations(habitat: str = Query("moon", description="iss | spacecraft | exploration | moon | rover | mars | custom"),
                        pillar: str | None = Query(None, description="prevention | detection | suppression | fundamental"),
                        gravity_g: float | None = Query(None, ge=0, le=1.0), o2_pct: float | None = Query(None, ge=5, le=100),
                        pressure_kpa: float | None = Query(None, ge=10, le=200)):
    """Rank all PSI investigations by relevance to a habitat. Every score has 4 named components and plain-language
    reasons; weights are returned. habitat=custom needs gravity_g, o2_pct and pressure_kpa."""
    from pipelines.common import HABITATS
    from .ranking import rank, RANK_WEIGHTS, METHOD
    if pillar and pillar not in PILLAR_VALUES:
        raise HTTPException(422, f"pillar must be one of {PILLAR_VALUES}")
    if habitat == "custom":
        if None in (gravity_g, o2_pct, pressure_kpa):
            raise HTTPException(422, "habitat=custom needs gravity_g, o2_pct and pressure_kpa.")
        hab = {"name": "Custom habitat", "kind": "custom", "gravity_g": gravity_g, "o2_pct": o2_pct, "pressure_kpa": pressure_kpa}
    elif habitat in HABITATS:
        hab = {k: v for k, v in HABITATS[habitat].items() if k != "in_missions"}
    else:
        raise HTTPException(404, f"Unknown habitat '{habitat}'. Use one of {sorted(HABITATS)} or custom.")
    rows = rank(list(_profiles().values()), hab, pillar)
    return {"habitat": {"key": habitat, **hab}, "weights": RANK_WEIGHTS, "method": METHOD.strip(),
            "caveat": "Relevance ranking of NASA investigations, not a probability of fire or a safety rating.", "ranked": rows}


@app.get("/api/datasets")
def datasets_catalog():
    """Gold datasets for predictive modeling: rows, real columns (with fill counts), caveats, download links."""
    from .insights import datasets
    return datasets()


@app.get("/api/datasets/{name}.csv", include_in_schema=True)
def dataset_download(name: str = Path_(..., max_length=60)):
    """Download one whitelisted Gold dataset as CSV (CC0, NASA PSI)."""
    from .insights import dataset_path
    p = dataset_path(name)
    if not p or not p.is_file():
        raise HTTPException(404, f"Unknown dataset '{name}'. See /api/datasets.")
    return FileResponse(p, media_type="text/csv", filename=f"astrofire_{name}.csv")


@app.get("/api/equipment-insights")
def equipment_insights():
    """Prevention / detection / suppression: NASA's own sentences about detectors, suppressants and material design."""
    from .insights import equipment
    return equipment()


@app.get("/api/earth-applications")
def earth_applications():
    """Earth applications: challenge spinoff resources + NASA's own Earth-benefit statements per investigation."""
    from .insights import earth
    return earth()


@app.get("/api/investigations/{investigation_id}/profile")
def investigation_profile(investigation_id: str = Path_(..., max_length=20)):
    p = _profiles().get(investigation_id.upper())
    if not p:
        raise HTTPException(404, f"Unknown investigation id '{investigation_id}'. See /api/investigations/profiles.")
    return p


@app.get("/api/materials")
def materials():
    """Material catalog: identity basis, investigations, test counts, available/missing properties."""
    return _rows("gold/powerbi/material_overview.csv")


@app.get("/api/material-families")
def material_families():
    """Solid-test counts per material family (named vs inferred identity). Used by the scenario picker."""
    return E.materials()


@app.get("/api/materials/{material_id}")
def material(material_id: str = Path_(..., max_length=80)):
    m = next((r for r in _rows("silver/materials/materials.csv") if r["material_id"] == material_id), None)
    if not m:
        raise HTTPException(404, f"Unknown material_id '{material_id}'. See /api/materials.")
    samples = [r for r in _rows("silver/materials/material_samples.csv") if r["material_id"] == material_id]
    props = [r for r in _rows("silver/materials/material_properties.csv") if r["material_id"] == material_id]
    ov = next((r for r in _rows("gold/powerbi/material_overview.csv") if r["material_id"] == material_id), {})
    return {"material": m, "overview": ov, "samples": samples[:200], "sample_count": len(samples), "properties": props[:500],
            "evidence_limitations": [x for x in [
                "Material not named in NASA table; family is a low-confidence candidate." if m["classification_basis"] != "explicit_name" else "",
                "No density, mass, composition or thermal properties in NASA tables.",
                "Pressure of ISS/Cygnus tests is assumed (~101 kPa), not measured."] if x]}


@app.get("/api/experiments")
def experiments(investigation_id: str = Query(..., max_length=20, description="e.g. PSI-25"), limit: int = Query(200, ge=1, le=1000),
                offset: int = Query(0, ge=0)):
    """Investigation-specific Silver records (each investigation keeps its own schema)."""
    if investigation_id not in SILVER_TABLES:
        raise HTTPException(404, f"No experimental table for {investigation_id}. Available: {sorted(SILVER_TABLES)}")
    rows = _rows(f"silver/investigations/{SILVER_TABLES[investigation_id]}.csv")
    return {"investigation_id": investigation_id, "total": len(rows), "records": [_clean(r) for r in rows[offset:offset + limit]]}


@app.get("/api/measurements")
def measurements(record_id: str | None = Query(None, max_length=80), quantity: str | None = Query(None, max_length=60),
                 limit: int = Query(500, ge=1, le=5000)):
    if not record_id and not quantity:
        raise HTTPException(400, "Give record_id or quantity.")
    rows = [r for r in _rows("silver/measurements/measurements.csv")
            if (not record_id or r["record_id"] == record_id) and (not quantity or r["quantity"] == quantity)]
    return {"total": len(rows), "measurements": rows[:limit]}


@app.get("/api/analytics/overview")
def analytics_overview():
    return {"kpis": _rows("gold/powerbi/kpis.csv"), "mission_coverage": _rows("gold/analytics/mission_coverage.csv"),
            "outcomes": _rows("gold/powerbi/outcome_summary.csv")}


@app.get("/api/droplets")
def droplets():
    """FLEX fuel-droplet flames on the ISS (Gold). Liquid fuel: never mixed into solid-material results."""
    return _rows("gold/analytics/droplet_extinction_tests.csv")


@app.get("/api/cool-flames")
def cool_flames():
    """CFI cool-flame droplet tests on the ISS (Gold): conditions only, no outcome recorded by NASA."""
    return _rows("gold/analytics/cool_flame_tests.csv")


@app.get("/api/gas-flames")
def gas_flames():
    """ACME gaseous flames on the ISS (CFI-G with NASA outcome codes, Flame Design conditions only) (Gold)."""
    return _rows("gold/analytics/gas_flame_tests.csv")


@app.get("/api/session-logs")
def session_logs():
    """PSI tables that are logs, not tests: ACME BRE / CLD / E-FIELD / s-Flame / SLICE test days, PSI-142 figure index, DAFT sessions."""
    return _rows("silver/investigations/acme_bre_sessions.csv") + _rows("silver/investigations/psi_session_logs.csv")


@app.get("/api/smoke")
def smoke(material_id: str | None = Query(None, max_length=80)):
    """SAME / SAME-R smoke from overheated (not burning) cabin materials (Gold)."""
    rows = _rows("gold/analytics/smoke_generation_tests.csv")
    return [r for r in rows if not material_id or r["material_id"] == material_id]


@app.get("/api/gas-jets")
def gas_jets():
    """SPICE gas-jet flame conditions (smoke point / soot) (Gold)."""
    return _rows("gold/analytics/gas_jet_flame_conditions.csv")


@app.get("/api/data-quality")
def data_quality():
    q = _rows("quarantine/quarantine.csv")
    from collections import Counter
    return {"tables": _rows("gold/powerbi/data_quality_overview.csv"),
            "quarantine": [{"investigation": a, "rule": b, "severity": c, "records": n}
                           for (a, b, c), n in Counter((r["investigation"], r["validation_rule"], r["severity"]) for r in q).items()]}


@app.get("/api/map")
def fmap(material: str | None = Query(None, max_length=80)):
    return E.flammability_map(material)


@app.post("/api/scenario")
def scenario(s: Scenario):
    if s.mission in MISSIONS:
        m = MISSIONS[s.mission]
        s.gravity_g, s.o2_pct, s.pressure_kpa = m["gravity_g"], m["o2_pct"], m["pressure_kpa"]
    return E.scenario(s.material, s.gravity_g, s.o2_pct, s.pressure_kpa, s.flow_cm_s)


class ParseIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


@app.post("/api/scenario/parse")
def scenario_parse(p: ParseIn):
    """Free text -> structured scenario (rule-based). Placeholder for the team chatbot; same output contract."""
    from .scenario_parse import parse
    return parse(p.text, [m["material"] for m in E.materials()])


@app.get("/api/gaps")
def gaps():
    return E.gaps()


# ---------------------------------------------------------------------------------------------
# Frontends. Registered LAST so every /api/* route, /docs and /openapi.json wins.
#   /      -> Gate 2 React app (frontend-app/dist, built with `npm run build`)
#   /lite  -> Gate 1 static app (frontend/), kept as a backup when present
# ---------------------------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
APP_DIST = ROOT / "frontend-app" / "dist"
LITE_DIR = ROOT / "frontend"

if LITE_DIR.is_dir():
    @app.get("/lite", include_in_schema=False)
    def lite_redirect():
        return RedirectResponse("/lite/")

    app.mount("/lite", StaticFiles(directory=LITE_DIR, html=True), name="lite")

if (APP_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=APP_DIST / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    """Serve the React single-page app; client-side routes (/scenario, /style ...) fall back to index.html."""
    if full_path.startswith("api/"):
        raise HTTPException(404, f"Unknown API route '/{full_path}'. See /docs.")
    index = APP_DIST / "index.html"
    if not index.is_file():
        return HTMLResponse("<h1>AstroFire</h1><p>Frontend not built. Run <code>cd frontend-app && npm install && npm run build</code>. "
                            "API docs: <a href='/docs'>/docs</a></p>", status_code=503)
    target = (APP_DIST / full_path).resolve()
    if full_path and target.is_file() and APP_DIST.resolve() in target.parents:
        return FileResponse(target)  # favicon.svg and other files from public/
    return FileResponse(index)
