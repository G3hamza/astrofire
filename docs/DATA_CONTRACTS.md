# Data Contracts (Phase 6)

Stable interfaces for each teammate. Nobody needs to open raw NASA files. Breaking changes require a version bump in `backend/app.py` and a note here.

## A. Backend developer
Read **Gold and Silver only**, through the FastAPI app (`uvicorn backend.app:app`). Interactive docs at `/docs`.

| Endpoint | Purpose | Params | Source | Errors |
|---|---|---|---|---|
| `GET /api/investigations` | Investigation list, dates, DOI, record counts | — | gold/powerbi/investigation_overview | — |
| `GET /api/materials` | Material catalog with identity basis, tests, properties available/missing | — | gold/powerbi/material_overview | — |
| `GET /api/materials/{material_id}` | One material: entity, samples, properties, evidence limitations | path id | silver/materials/* | 404 unknown id |
| `GET /api/material-families` | Test counts per family (named vs inferred) for pickers | — | gold solid_fire_tests | — |
| `GET /api/experiments?investigation_id=PSI-69&limit&offset` | Investigation-specific records (own schema) | id required | silver/investigations/* | 404 if no table (e.g. PSI-62) |
| `GET /api/measurements?record_id=&quantity=` | Long-format measurements with unit + status | one required | silver/measurements | 400 if neither |
| `GET /api/analytics/overview` | KPIs, mission coverage, outcome summary | — | gold/powerbi, gold/analytics | — |
| `GET /api/data-quality` | Per-table valid/warning counts + quarantine summary | — | gold/powerbi/data_quality_overview, quarantine | — |
| `POST /api/scenario` | Evidence-ranked scenario check | `{material, mission? (iss/exploration/moon/mars), gravity_g, o2_pct, pressure_kpa, flow_cm_s}` | gold solid_fire_tests + partial gravity | — |
| `GET /api/map`, `/api/gaps`, `/api/stats`, `/api/missions` | Flammability map points, coverage grid, counts | `material?` | gold | — |
| `POST /api/ask`, `GET /api/ask/status`, `/ai/*` | Evidence-grounded analyst (see docs/AI_LAYER.md) | `{question, habitat?, history?}` | gold/rag + engines | template answers without API key; 422 invalid input; 429 rate limit |

Example (`GET /api/materials/MAT-unnamed-black-rod`, real output, trimmed):
```json
{"material": {"material_id": "MAT-unnamed-black-rod", "material_family": "Unknown", "candidate_family": "PMMA (acrylic)",
  "classification_basis": "unknown_shape_only", "original_names": "0.5\" black rod | 1/4\" black rod | 3/8\" black rod",
  "investigations": "BASS-II"},
 "evidence_limitations": ["Material not named in NASA table; family is a low-confidence candidate.",
  "No density, mass, composition or thermal properties in NASA tables.", "Pressure of ISS/Cygnus tests is assumed (~101 kPa), not measured."]}
```
**Scenario contract (must be shown in the UI):** `verdict` ∈ {"Evidence suggests it burns", "Borderline in tested evidence", "Evidence suggests it goes out", "Insufficient validated experimental evidence"}; `evidence_status` (evidence-based / exploratory); `confidence`; `blockers[]` (why evidence is insufficient); `flags[]`; `nearby_burn_share` + `nearby_burn_share_note` ("NOT a calibrated probability" — never display as %, chance or probability); `gravity_bounds` (only when gravity > 0: `lower_bound` = PSI microgravity tests, `upper_bound` = NASA's 1 g comparison in Saffire-II, `bounds_cover_request`, `applies`, `partial_gravity_mimic` (E-FIELD), `coming_next` (LUCI, FM2); never a value for the requested gravity); `evidence[]` each with `source_file`, `source_row`, `psi_url`.

## B. AI / RAG developer
Input: `data/gold/rag/chunks.jsonl` (one JSON per line), **PSI-only** since v0.3 (the 307 NTRS papers were removed: outside the challenge data):
`chunk_id, document_id, chunk_index, char_start, char_end, page (null), title, year, url, topic, related_investigations[], content_type, text`
(+ `investigation_id, acronym, field, source_path`). `content_type` ∈ `nasa_text` (copied from PSI investigation.json), `computed_summary`
(computed from Gold tables), `challenge_resource` (the challenge's resources tab; background, not experimental evidence).
Document metadata: `data/gold/rag/documents.jsonl`. The AI layer is implemented in `ai/` — see **docs/AI_LAYER.md** for endpoints
(`POST /api/ask`, `GET /api/ask/status`, `POST /ai/{chat,ask,scenario,compare,gaps}`, `GET /ai/summary/{id}`, `GET /ai/health`) and shapes.
Rules: every answer cites evidence ids that map to a table row (source_file + source_row), a PSI URL or a chunk_id; verdicts come only
from the Scenario engine; no probabilities; BM25 retrieval by default, Chroma optional (keyed by `chunk_id`).

## C. AI / ML developer
`data/gold/ml/solid_outcome_features.csv` + `data/gold/ml/README.md`. Features, target, grouped split, missing-value policy and label reliability are defined there. Status: **not validated** (baseline below majority class). Do not present any model output as a prediction.

## D. Analytics / Power BI
Load `data/gold/powerbi/*.parquet` (or CSV) and `data/gold/analytics/*.parquet`.

| KPI (kpis.csv) | Formula | Unit |
|---|---|---|
| solid_flame_tests_total | count(solid_fire_tests) | tests |
| pct_tests_material_named | named / total × 100 | % |
| pct_outcomes_observed / pct_outcomes_inferred | basis count / total × 100 | % |
| o2_tested_min_pct / o2_tested_max_pct | min/max(o2_initial_pct) | % vol |
| space_tests_at_moon_mars_design_point | sum(mission_coverage.space_solid_tests_near) for Lunar+Mars | tests |
| droplet_tests_total, droplet_pressure_range_kpa | FLEX count, min–max pressure | tests, kPa |
| smoke_records_total, spice_unique_flame_conditions, materials_total, materials_unknown_identity | counts | — |

Dimensions: investigation, material_family_effective, material_identity, outcome_class, outcome_basis, quality_status, mission. Aggregation rule: never sum across Gold tables of different experiment kinds. Refresh: re-run the pipeline, then refresh the Power BI dataset (manual; no scheduler).

## E. Data engineering
See PIPELINE_GUIDE.md (add an investigation, add a file, run, validate, rebuild, versioning, recovery).
