# AstroFire — Space Fire Evidence Engine
**NASA Space Apps Cairo 2026 · Challenge: Flame in Freefall · Team Starry Night**

[![Live](https://img.shields.io/badge/live-astrofire.vercel.app-38D6F5)](https://astrofire.vercel.app)
[![Data](https://img.shields.io/badge/data-NASA%20PSI%20(CC0)-EA6624)](https://psi.nasa.gov)
[![CI](https://github.com/G3hamza/astrofire/actions/workflows/ci.yml/badge.svg)](https://github.com/G3hamza/astrofire/actions)

AstroFire turns NASA's space combustion experiments into fire-safety answers for spacecraft, the ISS, Moon and Mars bases
and rovers: **Will it burn? What proves it? How sure are we?** Every answer links to the NASA test behind it, and when
NASA never tested a case it says so: *"Insufficient validated experimental evidence."*

| | |
|---|---|
| **Project (live)** | https://astrofire.vercel.app · backup https://astrofire.vercel.app/lite/ · API https://astrofire.vercel.app/docs |
| **Proposal** | [`docs/PROPOSAL.md`](docs/PROPOSAL.md) ([PDF](docs/AstroFire_Proposal.pdf)) |
| **About / judging criteria** | https://astrofire.vercel.app/about |
| **Demo script** | [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) |
| **Handbook (beginners)** | [`docs/HANDBOOK.md`](docs/HANDBOOK.md) ([PDF](docs/AstroFire_Handbook.pdf)) |
| **Full technical context** | [`docs/CONTEXT.md`](docs/CONTEXT.md) |

### The finding
NASA's **263 solid-material space fire tests** all ran at **13.6–22.2 % oxygen, ~0 g** and normal cabin pressure.
Moon/Mars habitats are planned at **~34 % oxygen and 56.5 kPa**. **No solid cabin material in NASA PSI has been burned
at that atmosphere or at Moon/Mars gravity.** AstroFire shows what is known, what is not, and which experiments matter most.

### How it meets the judging criteria
| Criterion | In AstroFire |
|---|---|
| **Impact** | Fire safety for Artemis-era habitats with high-oxygen atmospheres; helps engineers, researchers, equipment designers, students; Earth spinoffs |
| **Creativity** | Refuses to guess at the edge of the evidence; gravity bounds from 0 g and 1 g NASA data; an AI that can only rewrite cited NASA evidence; habitat relevance ranking |
| **Validity** | Deterministic verdict engine; every row traceable to NASA file + row; observed / inferred / not-recorded labels; 139 automated tests; 26-question AI evaluation (0 probability violations, 100 % correct refusals) |
| **Relevance** | Built only on NASA PSI's 24 combustion investigations; covers every challenge objective: summarize / rank / interpret, most relevant investigations, data for modeling, equipment, Earth |
| **Presentation** | Ask in plain English or Arabic on any page; every number clickable to its source; About page, handbook and demo script |

### Use of AI (disclosure)
The app uses an open-weight language model (openai/gpt-oss-120b on Groq, with fallbacks) only to write answer text from
NASA evidence selected by deterministic code; guardrails block invented numbers, probabilities and changed verdicts, and
each answer says whether it was AI-written or a template. The team used AI coding assistants (Anthropic Claude) during
development. Details: [`docs/PROPOSAL.md` §10](docs/PROPOSAL.md#10-use-of-ai-disclosure).

## Screens
| Screen | Path | What it shows |
|---|---|---|
| Home | `/` | 263 solid tests vs the habitat atmosphere, closest real space flames, coverage per mission, "Why it matters" |
| Scenario check | `/scenario` | Inputs → verdict → blockers → flags → evidence table (PSI link + file#row) → why the gap exists + closest flames; describe in words. Moon/Mars: 0 g vs 1 g bounds (PSI microgravity tests vs NASA's Saffire-II 1 g comparison), E-FIELD as a partial-gravity mimic, LUCI/FM2 as coming next |
| Compare | `/compare` | 2–4 scenarios side by side, differences highlighted, shareable |
| Gaps map | `/gaps` | Gravity × O₂ × pressure: solid tests, flames-only cells, untested cells, mission points |
| Evidence charts | `/charts` | Flammability map (O₂ × air flow, by outcome) |
| Ask (AI analyst) | `/ask` | Questions answered from NASA PSI evidence: findings with clickable [E#] citations (record, file, row), interpretation kept separate, limits, follow-ups. Works without an API key (template mode). See `docs/AI_LAYER.md` |
| Habitat ranking | `/rank` | Pick spacecraft, ISS, Moon base, pressurized rover or Mars base: all 24 investigations ranked 0–100 with 4 named score parts (conditions 40, relevance 25, fuel 20, evidence 15) and plain reasons. Method: `backend/ranking.py` |
| Investigations | `/investigations` | All 24 PSI investigations: NASA objective/hypothesis/approach/impacts, fuels and conditions, what varied vs stayed the same, sensors, data files; filter by pillar (prevention / detection / suppression) and relevance; compare 2–6 side by side |
| NASA experiments | `/experiments` | All 24 PSI combustion investigations, FLEX/CFI/ACME charts, smoke, logs, challenge resources |
| Data and applications | `/applications` | Download 8 Gold datasets for flammability modeling (real columns, fill counts, caveats; CC0); NASA's own words on detection / suppression / material selection per pillar (interpretation labelled); Earth applications (challenge spinoffs + NASA Earth-benefit statements) |
| Materials · Data quality | `/materials`, `/data` | Named vs unknown materials; observed / inferred / missing |
| About | `/about` | The project by judging criteria, NASA data used, AI-use disclosure |
| Lite backup | `/lite/` | No-build version of Home, Scenario, Gaps |

**Data scope:** only NASA's PSI combustion repository and the pages on the Space Apps challenge resources tab. Features that needed
other sources (NTRS papers: drop-tower margins, paper-reported tests) were removed; the AI analyst uses a PSI-only knowledge base. How it all works: [`docs/HOW_IT_WORKS.md`](docs/HOW_IT_WORKS.md) (short) and the full guide [`docs/guide/`](docs/guide/README.md).

## Deploy
**Vercel (free, no card)** — production is https://astrofire.vercel.app. From the repo folder: `npx vercel@65.16.0 deploy --prod`.
`vercel.json` builds the React app and runs the FastAPI app (`api/index.py`) as one Python function that serves the UI, `/api/*`,
`/ai/*`, `/lite/` and `/docs`. AI keys go in Vercel → Settings → Environment Variables (`GROQ_API_KEY`, `LLM_PROVIDER`, `LLM_MODEL`,
`LLM_FALLBACKS`); without a key the analyst runs in template mode.

## Deploy with Docker (Render, Railway, Azure Container Apps)
The `Dockerfile` builds the React app, runs the pipeline and serves everything on `$PORT`. `render.yaml` is a ready Render Blueprint.
No API key is needed (the AI analyst runs in template mode; add a key in `.env` for AI-written answers, see `.env.example`). PSI data is CC0.

## Run it
```bash
pip install -r requirements.txt
python -m pipelines.orchestration.run_all   # Bronze → Silver → Gold → RAG → validation (≈30 s)
pytest -q                                   # data rules + API tests
uvicorn backend.app:app --reload            # API at http://127.0.0.1:8000/docs
```
App: `cd frontend-app && npm install --legacy-peer-deps && npm run build`, then the same `uvicorn` command serves it at http://127.0.0.1:8000/ (design system at `/style`). See `frontend-app/README.md`.

## Data layers
| Layer | Where | What |
|---|---|---|
| Bronze (immutable) | `data/raw/psi/` + `data/manifests/bronze_manifest.csv` | 24 NASA PSI investigations (CC0); SHA-256 + source URL per file |
| Silver | `data/silver/investigations/` | One cleaned table per investigation: BASS-II, BASS, SAFFIRE-I/II/III, SAME, SAME-R, FLEX, SPICE (full original row kept) |
| | `data/silver/materials/`, `measurements/`, `reference/` | Material entity (25), samples, properties, 6k+ measurements, Moon/Mars limits table |
| Quarantine | `data/quarantine/quarantine.csv` | Every rejected/suspicious row with reason + rule (nothing deleted) |
| Gold | `data/gold/analytics/`, `powerbi/`, `ml/`, `rag/` | Analytics tables, Power BI tables + KPIs, ML table (not validated), RAG documents/chunks |

CSV is the source of truth; every table also has a `.parquet` copy. Schemas: `schemas/`. `data/processed/` is a legacy export for the Kaggle notebook.

## Docs
`docs/PROJECT_AUDIT.md` · `CURRENT_ARCHITECTURE.md` · `TARGET_ARCHITECTURE.md` · `IMPLEMENTATION_GAPS.md` · `DATA_MODEL.md` · `ER_DIAGRAM.md` · `DATA_DICTIONARY.md` (auto) · `DATA_CONTRACTS.md` (API + team contracts) · `DATA_QUALITY_REPORT.md` (auto) · `PROVENANCE_REPORT.md` (auto) · `PIPELINE_GUIDE.md` · `SOURCES.md`

## Data honesty rules
- Every Silver/Gold row has `source_file` + `source_row`; every RAG chunk has `document_id` + `url`.
- `outcome_basis`: `observed` (NASA wrote it) vs `inferred` (derived from notes) vs `not_recorded`. Only observed outcomes are labels.
- Materials are classified only from names NASA wrote. Unnamed rods/spheres/films are `Unknown` (candidate PMMA, low confidence).
- Pressure for ISS/Cygnus tests is **assumed** 101.3 kPa (`pressure_status`). FLEX pressure is measured.
- Scenario results outside tested conditions (e.g. Moon, Mars, 34% O₂) return **"Insufficient validated experimental evidence"**, plus the cited partial-gravity reference data. Similarity shares are never shown as probabilities.
- Not built: Iceberg, MinIO, Snowflake, vector DB, Prometheus/Grafana (see `TARGET_ARCHITECTURE.md`).
- Licence: PSI files are CC0. NASA papers (NTRS), standards and Task Book files are not part of this public repo.
