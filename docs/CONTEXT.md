# AstroFire — full project context

One file that tells a new teammate, a reviewer or an AI assistant everything about AstroFire: what it is, why each
decision was made, how every part works, where everything lives, and what is still open.
Companion documents: **docs/HANDBOOK.md** (how to use, read and apply it, in plain words) and **docs/UI_CONTEXT.md**
(everything needed to redesign the UI). Last updated: 14 Nov 2026.

---

## 1. What AstroFire is

**AstroFire** is a web app for the NASA Space Apps Cairo 2026 challenge **"Flame in Freefall"** (Team Starry Night).
It turns NASA's **Physical Sciences Informatics (PSI)** combustion data into fire-safety answers for spacecraft, the
ISS, Moon and Mars bases and pressurized rovers.

It answers three questions from real NASA space fire tests: **Will it burn? What proves it? How sure are we?** — and
says plainly when NASA has no evidence: **"Insufficient validated experimental evidence."**

- Live app: **https://astrofire.vercel.app** (backup: `/lite/`, API docs: `/docs`)
- Code: **https://github.com/G3hamza/astrofire** (public, PSI data only)

### The headline finding
NASA ran **263 solid-material fire tests in space**, all at **13.6–22.2 % oxygen**, **~0 g** and assumed cabin pressure
(~101 kPa). Moon/Mars habitats are planned at about **34 % oxygen and 56.5 kPa** (inside the challenge's range of
"≥ 30 % O₂ at ≤ 10.2 psi / 70.3 kPa"). **No solid cabin material in PSI has been burned at that atmosphere or at
Moon (0.166 g) / Mars (0.38 g) gravity.** The challenge text itself confirms PSI has no partial-gravity combustion data.

### What the challenge asks, and where AstroFire answers it
| Challenge ask | Where |
|---|---|
| An "SI" (AI) dashboard that **summarizes, ranks and interprets** | Ask page + Ask AI panel (`/api/ask`), Rank page, Investigations page |
| **Identify investigations most relevant** to spacecraft, stations, Moon/Mars bases, rovers | `/rank` (`/api/rank`) |
| **Extract data for predictive modeling** | `/applications` → 8 downloadable datasets (`/api/datasets`) |
| **Research for next-generation fire-safety equipment** | `/applications` → prevention / detection / suppression (`/api/equipment-insights`) |
| **Fire safety on Earth** | `/applications` → spinoffs + NASA Earth-benefit statements (`/api/earth-applications`) |
| Objectives, fuels, sample size, O₂, air flow, what varied, sensors | `/investigations` (`/api/investigations/profiles`) |
| Similarities and differences between investigations | `/investigations` compare, `/api/investigations/compare`, hardware groups |
| Partial gravity: "micro- and normal-gravity results could bound" it | Scenario → gravity bounds card (`gravity_bounds`), E-FIELD mimic, LUCI/FM2 "coming next" |
| Apollo 1, Apollo 13, Mir | Home → "Why it matters" |

---

## 2. Rules the whole project follows (non-negotiable)

1. **PSI data only** (+ the challenge's resources tab). NASA papers (NTRS), standards and Task Book files were removed
   from the app and from the public repo (kept privately in `../_private_archive`, outside the repo).
2. **Every fact has a source**: test rows carry `source_file` + `source_row`; passages carry `chunk_id` + URL; the UI
   links to the PSI page.
3. **Never invent**: no probabilities, no confidence percentages, no made-up numbers, no default materials. Unknown stays unknown.
4. **Observed ≠ inferred**: `outcome_basis` is `observed` (NASA wrote it), `inferred` (derived from NASA notes) or
   `not_recorded`. Only observed outcomes are labels. Pressure of ISS/Cygnus solid tests is **assumed**, not measured.
5. **Verdicts come from deterministic rules**, never from the LLM. The AI only explains evidence it is given.
6. **Secrets stay local**: `.env` is git-ignored, Docker-ignored and Vercel-ignored; keys live only in `.env` and in the
   host's secret store.

---

## 3. Architecture (end to end)

```
NASA PSI files (data/raw/psi, CC0)
   │  pipelines/ingestion/manifest.py      Bronze: SHA-256 + source URL per file (data/manifests/bronze_manifest.csv)
   ▼
pipelines/transformation/silver.py        Silver: one cleaned table per investigation + materials + measurements
   │                                       bad rows → data/quarantine/quarantine.csv (never deleted)
   ▼
pipelines/transformation/gold.py          Gold: analytics tables, Power BI tables, ML table
pipelines/transformation/profiles.py      Gold: 24 investigation profiles (json + csv)
pipelines/transformation/rag.py           Gold: PSI-only knowledge base (234 passages)
pipelines/validation/                     validate.py (47 checks → docs/DATA_QUALITY_REPORT.md, PROVENANCE_REPORT.md),
                                          dictionary.py (docs/DATA_DICTIONARY.md)
   ▼
backend/ (FastAPI)                        engine.py (scenario, gaps, gravity bounds), ranking.py, compare.py,
                                          insights.py (datasets, equipment, Earth), scenario_parse.py (free text)
ai/ (AI layer, same FastAPI app)          retrieval (BM25) → tools → evidence registry → template or LLM → guardrails
   ▼
frontend-app/ (React + Vite + TS + Tailwind + Recharts)  built to frontend-app/dist, served by FastAPI at "/"
frontend/ (no-build backup)                served at /lite
```

Run everything: `python -m pipelines.orchestration.run_all` (≈ 30 s) → `pytest -q` → `uvicorn backend.app:app`.

### Tech stack
| Layer | Tools |
|---|---|
| Data pipeline | Python 3.12/3.13, pandas, csv (CSV is the source of truth; Parquet copies via pyarrow, optional) |
| API | FastAPI, Pydantic, Uvicorn |
| AI | LangChain (`init_chat_model`), Groq (`openai/gpt-oss-120b` + fallbacks), rank-bm25, python-dotenv; optional Anthropic |
| Frontend | React 18, Vite 5, TypeScript, Tailwind 3, Recharts, React Router, lucide-react icons |
| Tests | pytest (138 tests, 10 files), FastAPI TestClient, fake LLM for offline AI tests |
| CI | GitHub Actions: `data-pipeline` (pipeline + build + tests), `docker-image` (publishes ghcr.io/g3hamza/astrofire) |
| Hosting | Vercel (free, `vercel.json` + `api/index.py`); Dockerfile also works on Render/Railway/Azure |

---

## 4. Data

### Source
24 PSI combustion investigations (CC0). In-scope list and roles: `pipelines/common.py` `INVESTIGATIONS`.

### Gold tables (what the app reads)
| Table | Rows | What a row is |
|---|---|---|
| `gold/analytics/solid_fire_tests.csv` | 263 | One solid-material space test (BASS 121, BASS-II 129, Saffire I 2, II 9, III 2) |
| `gold/analytics/droplet_extinction_tests.csv` | 274 | FLEX fuel-droplet flame (methanol/heptane; diluent N₂/CO₂/He) |
| `gold/analytics/cool_flame_tests.csv` | 79 | CFI cool-flame droplet test (conditions only) |
| `gold/analytics/gas_flame_tests.csv` | 660 | ACME CFI-G (333) + Flame Design (327) gas flames, O₂ 12–85 % |
| `gold/analytics/smoke_generation_tests.csv` | 117 | SAME (8) / SAME-R (109) smoke from heated (not burning) materials |
| `gold/analytics/gas_jet_flame_conditions.csv` | 435 | SPICE gas-jet flame conditions |
| `gold/analytics/investigation_profiles.json/.csv` | 24 | One profile per investigation (see §6) |
| `gold/analytics/mission_coverage.csv` | 4 | Space tests near each mission design point |
| `gold/ml/solid_outcome_features.csv` | 33 | ML table: solid tests with NASA-written outcomes only. **Not validated** |
| `gold/powerbi/*` | — | KPIs, overviews, outcome summary, data-quality overview |
| `gold/rag/chunks.jsonl` / `documents.jsonl` | 234 / 26 | AI knowledge base (see §7) |

Outcome basis across the 263 solid tests: **39 observed, 101 inferred, 123 not recorded.**

### Curated team classification
`data/curation/investigation_curation.csv` — per investigation: `pillar` (prevention / detection / suppression /
fundamental), `relevance_tier` (direct / related / background), `hardware_family`, `fuel_phase`, `study_type`,
`partial_gravity_note`, and a **`curation_basis` quoting the challenge text**. Direct = named by the challenge as a
flammability (BASS, BASS-II, Saffire I–III), detection (SAME, SAME-R) or suppression (FLEX) study.

---

## 5. The scenario engine (`backend/engine.py`)

Input: `material, gravity_g, o2_pct, pressure_kpa, flow_cm_s` (or a `mission` preset).
1. Find the 8 closest solid tests by **evidence distance**: Euclidean distance over scaled differences
   (gravity ÷ 0.1 g, O₂ ÷ 2 points, pressure ÷ 15 kPa, flow ÷ 5 cm/s), +1.5 if a different material.
2. **Blockers** (any one ⇒ verdict "Insufficient validated experimental evidence"): requested gravity never tested;
   O₂ outside 13.6–22.2 %; pressure more than 15 kPa from ~101 kPa; no test of that material nearby.
3. Otherwise a similarity-weighted share of nearby tests that burned gives the verdict: "Evidence suggests it burns" /
   "Borderline in tested evidence" / "Evidence suggests it goes out". The share is **never shown as a probability**.
4. Adds: 5 evidence rows (with file + row + PSI link), flags (inferred outcomes, unnamed materials, assumed pressure),
   `why_untested` explanations, `atmosphere_evidence` (closest FLEX/CFI droplet and ACME gas flames at that O₂ and
   pressure — never material evidence), and for gravity > 0: **`gravity_bounds`**:
   - lower bound = PSI microgravity tests of that material (count, outcomes, outcome basis, O₂ range);
   - upper bound = NASA's own **1 g comparison in Saffire-II** (`one_g_burn_length` vs microgravity burn length, 9 samples);
   - `bounds_cover_request`: true only if both ends exist at the requested O₂ and pressure; otherwise the text says the
     bounds do not cover the scenario;
   - E-FIELD Flames shown as a partial-gravity **mimic** (gas flames), LUCI and FM2 as "coming next to PSI".

Free text (`/api/scenario/parse`, `backend/scenario_parse.py`): reads material, mission, O₂, pressure (kPa/psi/atm/bar),
gravity and flow from a sentence; reports what it understood and what it defaulted.

---

## 6. Investigation profiles (`pipelines/transformation/profiles.py`)

For each of the 24 investigations: NASA's objective, hypothesis, approach, research impacts, hardware, dates, DOI,
publications (copied from `investigation.json`, `field_basis = nasa_text`); conditions computed from the tables (ranges or
values, which factors **varied** vs stayed **constant**, which were **not recorded**); outcomes by class and basis;
sensors and measured quantities (keyword matches on NASA text, with the matched sentence as evidence); PSI data files
(count, GB, file types); plus the curated pillar / tier / hardware / fuel / study type.

## 7. Habitat ranking (`backend/ranking.py`)

Habitats (one definition: `pipelines/common.py` `HABITATS`): ISS cabin & crew spacecraft 21 % / 101.3 kPa / 0 g;
exploration atmosphere 34 % / 56.5 kPa / 0 g; Moon base & pressurized rover 34 % / 56.5 kPa / 0.166 g; Mars base
34 % / 56.5 kPa / 0.38 g. Score 0–100 = **conditions 40 + relevance 25 + fuel 20 + evidence 15**:
- conditions: O₂ closeness (0 at 10 points away) × 0.45 + pressure (0 at 50 kPa) × 0.35 + gravity × 0.20
  (same gravity 1; ~0 g data for Moon/Mars = 0.5 because it only bounds partial gravity);
- relevance: direct 1, related 0.6, background 0.25; fuel: solid 1, smoke 0.9, dust 0.5, gas/droplet 0.4;
- evidence: flight records 0.5 + 0.5 × share of NASA-observed outcomes; ground analysis 0.3; models 0.2.
Every row returns its 4 components and plain reasons. It is a relevance order, **not** a safety rating.

---

## 8. The AI layer (`ai/`, details in docs/AI_LAYER.md)

- **Knowledge base**: 234 PSI-only passages — 136 `nasa_text` (NASA's own words), 87 `computed_summary` (from Gold
  tables + a cross-investigation overview), 11 `challenge_resource` (spinoffs, incidents, habitat atmosphere, partial
  gravity status). Fields keep data contract (B).
- **Retrieval**: BM25 (rank-bm25), tokenizer keeps `BASS-II`, `SAME-R`, `CFI-G` whole and as parts. Optional hybrid
  with local embeddings + Chroma (not used in production; nothing is ever downloaded automatically).
- **Router** (`ai/chat.py`): rule-first intents — `about` (greetings / "what are you"), `scenario`, `rank`, `compare`,
  `gaps`, `summary`, `datasets`, `earth`, `equipment`, `fabrication`, `ask`, `out_of_scope`; LLM classifies only if rules
  find nothing. Conversation memory: last 6 turns; follow-ups like "what did it vary?" resolve to the last investigation.
- **Tools** (`ai/tools.py`): search_investigations, get_investigation, search_records, rank_habitat, run_scenario,
  compare_investigations, research_gaps, search_passages, list_datasets. Each adds **evidence items** E1, E2 … with real
  file/row, PSI URL or chunk id.
- **Answer**: deterministic template first; if an LLM is configured it rewrites from the evidence in the format
  ANSWER / FINDINGS / INTERPRETATION / LIMITS / FOLLOWUPS. **One LLM call per question.**
- **Guardrails** (`ai/guardrails.py`, applied in every feature): no probability/likelihood/confidence wording
  (regenerate once, then strip); every number must appear in the evidence (rounding + kPa/psi tolerance; test ids
  ignored) else regenerate once then template; citations to unknown E-ids dropped and reported; scenario answers always
  state the engine verdict and start with "Insufficient validated experimental evidence." when required; prompt-injection
  text removed; keys redacted; off-topic → exact string "No data in the NASA papers provided."; output normalized to
  plain text.
- **Models**: `LLM_PROVIDER=groq`, `LLM_MODEL=openai/gpt-oss-120b` (reasoning effort low). `ModelChain` failover:
  primary → `LLM_FALLBACKS` (`groq:qwen/qwen3.8-27b, groq:openai/gpt-oss-20b`, optionally `anthropic:claude-haiku-5-5`)
  → template. Every skipped model is reported (`skipped:<model>:<error>`), `model` names who answered.
  Groq free tier: 200,000 tokens/day per model + per-minute limits.
- **Evaluation** (`python -m ai.eval.run`, 26 questions): template mode 100 % facts, 96 % citations, 100 % refusals,
  100 % insufficient-evidence, 0 probability violations. Live (Groq) run: 83 % facts, 96 % citations, 100 % refusals and
  insufficient-evidence, 0 probability violations. Report: `ai/eval/report.md`.

---

## 9. API (all JSON; interactive docs at `/docs`)

Data and engines (`backend/app.py`):
`GET /api/stats` · `/api/missions` · `/api/habitats` · `/api/investigations` · `/api/investigations/profiles?pillar=&tier=` ·
`/api/investigations/{id}/profile` · `/api/investigations/compare?ids=PSI-25,PSI-69` · `/api/hardware-groups` ·
`/api/rank?habitat=moon&pillar=` (or `habitat=custom&gravity_g=&o2_pct=&pressure_kpa=`) · `/api/materials` ·
`/api/materials/{id}` · `/api/material-families` · `/api/experiments?investigation_id=` · `/api/measurements` ·
`/api/analytics/overview` · `/api/droplets` · `/api/cool-flames` · `/api/gas-flames` · `/api/gas-jets` · `/api/smoke` ·
`/api/session-logs` · `/api/data-quality` · `/api/map?material=` · `/api/gaps` · `/api/datasets` ·
`/api/datasets/{name}.csv` · `/api/equipment-insights` · `/api/earth-applications` ·
`POST /api/scenario` · `POST /api/scenario/parse`.

AI (`ai/api.py`): `POST /api/ask` `{question, habitat?, history?}` → `answer, findings[], interpretation[], limits[],
followups[], tools_used[], mode ("ai"|"template"), model, intent, evidence[], sources[], insufficient_evidence,
guardrails[], request_id, latency_ms` · `GET /api/ask/status` · `POST /ai/chat` · `POST /ai/ask` · `POST /ai/scenario` ·
`POST /ai/compare` · `POST /ai/gaps` · `GET /ai/summary/{id}` · `GET /ai/health`.

Input limits (422 otherwise): gravity 0–1.5 g, O₂ 0–100 %, pressure 1–600 kPa, flow 0–200 cm/s, known mission,
material 1–80 chars, free text 1–1000 chars, questions ≤ 2000 chars, history ≤ 20 turns. AI rate limit 20/min per
visitor (by `X-Forwarded-For`). Errors are JSON with `request_id`, never stack traces. Security headers on every response.

---

## 10. Frontend (details in docs/UI_CONTEXT.md)

13 screens: Home, Scenario, Compare, Gaps, Charts, Ask, Rank, Investigations, Experiments, Materials (+ detail),
Apply (data & applications), Quality, Style (design system); plus a floating **Ask AI** panel on every page and the
no-build `/lite` backup. The current UI is functional on purpose; a redesign is planned and should only call the API above.

---

## 11. Deployment and operations

- **Vercel** (live): `vercel.json` builds `frontend-app`; `api/index.py` exposes the FastAPI app, which serves the React
  build, `/lite`, `/api/*`, `/ai/*`, `/docs`. Python deps from `requirements.txt` (runtime only); `requirements-dev.txt`
  adds pytest, httpx, pyarrow. `.vercelignore` blocks `.env` and local files. Env vars in Vercel (Production, secret):
  `LLM_PROVIDER`, `LLM_MODEL`, `LLM_FALLBACKS`, `GROQ_API_KEY`.
  Deploy after changes: `npx vercel@65.16.0 deploy --prod` from the repo folder (GitHub auto-deploy is not linked).
- **Docker**: `Dockerfile` (multi-stage: build UI → install → run pipeline → uvicorn with `--proxy-headers`);
  `docker-compose.yml` reads an optional `.env`; image published to `ghcr.io/g3hamza/astrofire` on every push.
- **Local**: `uvicorn backend.app:app --port 8000` → http://127.0.0.1:8000. `.env` (see `.env.example`) enables the LLM;
  without keys everything still works in template mode.
- **Cold start** on Vercel ≈ 3 s (startup loads only data + BM25, no LLM calls).

---

## 12. History (what was built, in order)

1. **Gate 1**: pipeline (Bronze/Silver/Gold), scenario engine, lite app.
2. **Gate 2**: React app (Home, Scenario, Compare, Gaps, Charts, Experiments, Materials, Quality), Docker, CI, demo script.
3. **PSI-only decision**: NTRS-paper features removed; all 24 PSI investigations integrated.
4. **Phase 0–1**: audit against the challenge; investigation profiles + `/investigations`.
5. **Phase 2**: habitat ranking (6 habitats) + `/rank`.
6. **Phase 3**: AI layer (PSI knowledge base, BM25, tools, guardrails, router, `/api/ask`, `/ai/*`, Ask page, eval).
   Live on Groq (`llama-3.3-70b-versatile` unavailable to the key → `openai/gpt-oss-120b`), failover chain.
7. **Phase 4**: Moon/Mars gravity bounds, E-FIELD mimic, LUCI/FM2; NTRS tables removed.
8. **Phase 5**: datasets for modeling, equipment insights, Earth applications + `/applications`.
9. **Phase 6**: input limits, error handling, security headers, proxy-aware rate limit, journey tests, secret scan.
10. **Public release**: non-PSI files stripped, clean single-commit history, public GitHub repo, CI green.
11. **Hosting**: Render and Hugging Face/Azure needed a card or paid plan → **Vercel** (free) via CLI.
12. **UX**: Ask box on Home, Ask AI panel on every page, free-text scenario open by default, greetings answered.

---

## 13. Open items / known limitations

- Demo video and submission text not done yet.
- GitHub → Vercel auto-deploy not linked (Vercel would not attach the GitHub login); deploy with the CLI.
- Groq free-tier limits: heavy use falls back to template answers (by design, never an error).
- Claude Haiku fallback configured but inactive (no valid Anthropic key with credits).
- Retrieval is lexical (BM25); embeddings optional.
- No PSI partial-gravity data exists; Moon/Mars answers are bounded, never predicted.
- ML table is small (33 labels) and not validated; never presented as a prediction.
- `notebooks/astrofire_analysis.py` still expects removed NTRS files.
- Vercel recommends enabling 2FA on the account.

## 14. Where things are
| Need | File |
|---|---|
| Plain-language guide | docs/HANDBOOK.md, docs/guide/, docs/pdf/ |
| UI redesign brief | docs/UI_CONTEXT.md |
| AI details | docs/AI_LAYER.md |
| API + team contracts | docs/DATA_CONTRACTS.md |
| Column meanings | docs/DATA_DICTIONARY.md (auto) |
| Data quality / provenance | docs/DATA_QUALITY_REPORT.md, docs/PROVENANCE_REPORT.md (auto) |
| Demo | docs/DEMO_SCRIPT.md |
| Sources | docs/SOURCES.md |
