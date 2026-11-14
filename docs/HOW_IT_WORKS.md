# AstroFire — how the prototype works (short version for the team)

> **Full, detailed guide (domain knowledge, data, engine, backend, UI, AI, testing, deployment):** [`docs/guide/`](guide/README.md)

**What it is:** a web app that answers *"Will this material burn in this habitat? What proves it? How sure are we?"* using only
NASA's PSI combustion data, and says plainly where that data stops (Moon/Mars gravity, 34% O₂, 56.5 kPa).

**Run it:** `pip install -r requirements.txt` → `python -m pipelines.orchestration.run_all` → `cd frontend-app && npm install --legacy-peer-deps && npm run build` → back in the root `uvicorn backend.app:app` → http://127.0.0.1:8000/

```
NASA PSI files ──► pipelines/ (Bronze → Silver → Gold, validated) ──► data/gold ──► backend/ (FastAPI + engine) ──► /api/*
                                                                                                         │
                                                         frontend-app/ (React, served at /)   frontend/ (/lite backup)
```

---

## 1. Data (sources and scope)
| Item | Detail |
|---|---|
| Allowed sources | Only what the Space Apps challenge resources page links: the **PSI combustion repository** + NASA pages (Apollo 1/13, Mir, spinoffs, background) |
| PSI investigations used | **All 24** combustion investigations, in `data/raw/psi/` (CC0). Downloaded tables + metadata only (36 MB); the 255 GB PSI totals are videos/photos of the same tests |
| What each gives | **Solid-material burns:** BASS, BASS-II, SAFFIRE I–III (263 tests) · **Droplet flames:** FLEX (274), CFI (79), FLEX-2 (test matrix) · **Gas flames:** ACME CFI-G (333, with outcomes), ACME Flame Design (327) · **Smoke:** SAME, SAME-R · **Soot:** SPICE · **Logs/indexes:** ACME BRE, CLD, E-FIELD, s-Flame, SLICE, PSI-142, DAFT · **No data table:** PSI-60, 62, 115, 117 |
| Removed (not on the challenge page) | NTRS papers: Ask NASA / RAG, drop-tower Moon/Mars margins, paper-reported tests (Saffire IV–VI, LUCI). Files still in `data/raw/ntrs` and `data/curated`, **not read by the app** |
| Mission design points | `backend/engine.py → MISSIONS`: ISS 21%/101.3 kPa/0 g; Exploration, Moon, Mars 34%/56.5 kPa at 0 / 0.166 / 0.38 g |

## 2. Data engineering (pipeline)
| Layer | What happens | Where |
|---|---|---|
| Bronze | Raw NASA files, never edited; SHA-256 + URL per file in a manifest | `data/raw/`, `data/manifests/bronze_manifest.csv`, `pipelines/ingestion/` |
| Silver | One clean table per investigation; original row kept (`source_record`); units normalized (mmHg/atm/bar → kPa, fractions → %); every value tagged observed / inferred / assumed; bad rows quarantined, never deleted | `pipelines/transformation/silver.py`, `data/silver/`, `data/quarantine/` |
| Gold | Analysis tables the app reads: `solid_fire_tests`, `droplet_extinction_tests`, `cool_flame_tests`, `gas_flame_tests`, `smoke_generation_tests`, `gas_jet_flame_conditions`, mission coverage, KPIs | `pipelines/transformation/gold.py`, `data/gold/` |
| Validation | 47 checks (schemas, ranges, required fields, vocabularies, duplicates, file hashes); run fails if any fails | `pipelines/validation/validate.py`, `docs/DATA_QUALITY_REPORT.md` |
| Data fixes found | CFI: 8 duplicated rows quarantined · ACME CFI-G: 861 blank rows skipped · BRE: "3400%"→34 typos · s-Flame "N3/N4"→N2 · CFI-G "Hot ignition" not used (contradicted burn times) | quarantine + `quality_notes` columns |
| One command | `python -m pipelines.orchestration.run_all` (≈30 s) | `pipelines/orchestration/run_all.py` |

## 3. Data analysis (the engine, no ML)
All in `backend/engine.py`. Rule-based and explainable; **never outputs a probability**.
| Function | How it works |
|---|---|
| `scenario()` | Distance from your scenario to every solid test: gravity /0.1 g, O₂ /2 points, pressure /15 kPa, flow /5 cm/s (+1.5 if a different material). Takes the 8 closest; similarity-weighted share that burned → "mostly burned / mixed / mostly went out" |
| Verdict | **Blockers** (gravity never tested, O₂ outside 13.6–22.2%, pressure ≠ ~101 kPa, no test of this material nearby) → *"Insufficient validated experimental evidence"*. Otherwise "Evidence suggests it burns / goes out" or "Borderline", with High/Medium/Low confidence from distance + flags |
| Shown as counts | "Closest tests: X of Y burned", never a % (SRS FR2.7) |
| `why_untested()` | Explains each blocker (gravity / oxygen / pressure) with a PSI source link |
| `atmosphere()` | Closest **droplet** flames (FLEX/CFI) and **gas** flames (ACME) at the same O₂ + pressure. Shown separately; never counted as material evidence, never changes a verdict |
| `gaps()` | Gravity × O₂ bins × pressure bins → solid tests per cell, plus droplet and gas-flame counts, mission design points |
| `flammability_map()` | BASS-II points (O₂ × air flow) with outcome and observed/inferred basis |
| Coverage KPI | Solid tests "near" a mission = same gravity, O₂ ±2 points, pressure ±15 kPa (`gold.py → coverage`) |

## 4. AI
| Part | Status |
|---|---|
| Free-text scenario ("Nomex on Mars at 34% oxygen and 8.2 psi") | **Rule-based parser, no AI model**: `backend/scenario_parse.py`, `POST /api/scenario/parse`. Reads material, mission, O₂, pressure (psi/atm/bar/hPa → kPa), gravity, flow (m/s, mm/s → cm/s); reports what it understood, what it defaulted, and warns about untested materials |
| Chatbot (team) | Plugs into the same contract: send text to `/api/scenario/parse`, or produce the same JSON and call `POST /api/scenario` |
| LLM answers / RAG | **Removed** with the NTRS papers. No API key, no external AI calls in the app |
| ML model | None. `data/gold/ml/` exists from earlier work but is **not validated** and not used |

## 5. Backend / API
FastAPI (`backend/app.py`), Python 3.13, reads only `data/gold` and `data/silver`. Interactive docs: `/docs`. All calls < 15 ms locally.
| Endpoint | Used by |
|---|---|
| `GET /api/stats`, `/api/analytics/overview`, `/api/missions` | Home |
| `POST /api/scenario`, `POST /api/scenario/parse`, `GET /api/material-families` | Scenario, Compare |
| `GET /api/gaps` | Gaps |
| `GET /api/map` | Charts |
| `GET /api/investigations`, `/api/droplets`, `/api/cool-flames`, `/api/gas-flames`, `/api/smoke`, `/api/gas-jets`, `/api/session-logs`, `/api/experiments?investigation_id=` | Experiments, evidence drawer |
| `GET /api/materials`, `/api/materials/{id}`, `/api/data-quality`, `/api/measurements` | Materials, Data quality |
| `/` and `/lite/` | Serve the React app and the backup app |

## 6. UI
| Item | Detail |
|---|---|
| Stack | React 18 + Vite 5 + TypeScript + Tailwind 3, Recharts (charts), lucide-react (icons), React Router. `frontend-app/` |
| Design system | Dark "mission control" theme, tokens in `src/index.css` + `tailwind.config.js`; all components on `/style` |
| Screens | Home · Scenario · Compare · Gaps · Charts · Experiments · Materials · Data quality (+ `/style`, 404). Pages in `src/pages/`, shared parts in `src/components/` |
| Scenario layout (SRS order) | Inputs (4 sliders always editable) → verdict + confidence + status → "X of Y burned" → red blockers → amber flags → evidence table (test, investigation, material, O₂, flow, outcome, basis, PSI link, file#row) → why the gap exists + closest flames |
| Honesty in the UI | Icons + words for outcomes (not color only), observed/inferred/assumed badges, source chip on evidence, "not available" instead of invented values |
| Accessibility | Colorblind-checked outcome palette (dataviz validator), keyboard focus, table view for charts, works at 1366×768 and 375 px |
| Data access | Typed client `src/lib/client.ts` + types `src/lib/types.ts`; cached `useQuery` hook `src/lib/api.ts`; only `/api/*` |
| Backup app | `frontend/` (plain HTML/CSS/JS, no build, no internet) at `/lite/`: Home, Scenario, Gaps |

## 7. Testing and quality
| Item | Detail |
|---|---|
| Tests | 40 pytest tests in `tests/`: data rules, every endpoint, scenario safety, demo flow, PSI coverage (24/24), ACME outcome mapping, no-paper-data guard, no "probability" wording in UI, app routes, `/lite` |
| Run | `python -m pipelines.orchestration.run_all` then `pytest -q` |
| CI | `.github/workflows/ci.yml`: pipeline + frontend build + tests on every push (not run yet: no GitHub repo) |

## 8. Deployment
| Item | Status |
|---|---|
| Docker | Multi-stage `Dockerfile` (build React → run pipeline → serve on `$PORT`). Not test-built (no Docker on this laptop) |
| Render | `render.yaml` blueprint, no secrets needed |
| Status | **Not deployed**, no GitHub repo yet |

## 9. Where to enhance next (ideas)
1. Deploy (GitHub → Render) and record the demo video.
2. Chatbot: connect to `/api/scenario/parse`; show what it understood.
3. Smoke results: parse SAME/SAME-R raw particle files from PSI (in Colab, not on Wi-Fi) for real smoke numbers per material.
4. Video-derived data: flame spread rates from BASS-II videos (PSI raw data) to add a measured quantity.
5. Engine: weight evidence by outcome basis (observed > inferred); tune distance scales with the team.
6. UI: projector test, outsider 10-second test, polish mobile tables.

## 10. Glossary
**PSI** NASA Physical Sciences Informatics data archive · **Bronze/Silver/Gold** raw / cleaned / analysis-ready data ·
**Observed / inferred / assumed** NASA wrote it / derived from NASA notes / stated assumption (e.g. ISS pressure ~101 kPa) ·
**Blocker** a reason NASA's tests can't answer a scenario · **SE / FT** ACME codes: self-extinguished / flow terminated while burning ·
**Exploration atmosphere** 34% O₂ at 56.5 kPa (8.2 psia).
