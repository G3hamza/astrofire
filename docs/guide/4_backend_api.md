# 4. Backend and API

## 4.1 What the backend is

**🧒 Simple version.** The backend is a program that runs on a computer (the "server"). The website asks it questions over the
internet, like *"give me the gaps map"* or *"check Nomex on Mars"*, and it answers with data. The website never reads NASA files
itself; it always asks the backend.

**🛠️ Engineer version.**
- **Python 3.13** (Docker uses 3.12) with **FastAPI 0.162** (web framework), **Uvicorn 0.54** (server), **Pydantic 2** (request
  validation).
- Code: `backend/app.py` (routes), `backend/engine.py` (logic, chapter 3), `backend/scenario_parse.py` (free-text parser, chapter 6).
- The `Engine` loads the Gold CSVs **once at startup** into memory; requests then take **4–15 ms**.
- It reads only `data/gold` and `data/silver`, never raw files (SRS rule NFR8).
- Start: `uvicorn backend.app:app` → http://127.0.0.1:8000. Interactive API docs (auto-generated): **/docs**.

## 4.2 Every endpoint

| Method & path | Returns | Used by |
|---|---|---|
| `GET /api/stats` | Counts: solid tests, tests with conditions, observed outcomes, investigations, droplet/gas flame tests, O₂ range | Home, design page |
| `GET /api/analytics/overview` | KPIs, mission coverage, outcome summary | Home, Data quality |
| `GET /api/missions` | The 4 mission atmospheres (ISS, Exploration, Moon, Mars) | Everywhere |
| `GET /api/material-families` | Materials with test counts (named vs inferred) | Scenario, Compare pickers |
| `POST /api/scenario` | The full answer: verdict, evidence, blockers, flags, why untested, atmosphere evidence | Scenario, Compare, Home |
| `POST /api/scenario/parse` | Free text → structured scenario | "Describe it in words", future chatbot |
| `GET /api/gaps` | 40 grid cells with counts and mission points | Gaps |
| `GET /api/map?material=` | BASS-II flammability points | Charts |
| `GET /api/investigations` | All 24 investigations with record counts | Experiments |
| `GET /api/experiments?investigation_id=PSI-25&limit=&offset=` | Raw cleaned Silver rows of one investigation | Evidence drawer, FLEX-2 table |
| `GET /api/droplets`, `/api/cool-flames`, `/api/gas-flames` | FLEX, CFI, ACME Gold tables | Experiments |
| `GET /api/smoke?material_id=`, `/api/gas-jets` | SAME/SAME-R, SPICE | Experiments, Materials |
| `GET /api/session-logs` | ACME BRE/CLD/E-FIELD/s-Flame, SLICE, PSI-142, DAFT rows | Experiments |
| `GET /api/materials`, `/api/materials/{id}` | Material catalog, one material with samples and limitations | Materials |
| `GET /api/data-quality` | Valid/warning per table, quarantine summary | Data quality |
| `GET /api/measurements?record_id=` | Long-format measurements | (available, not on a screen) |
| `GET /`, any page path | The React app (`frontend-app/dist/index.html`) | Browser |
| `GET /lite/` | The backup app (`frontend/`) | Browser |

Removed (data not on the challenge page): `/api/ask`, `/api/search`, `/api/partial-gravity`, `/api/literature-tests` (now 404,
checked by a test).

## 4.3 Example: checking a scenario

Request:
```http
POST /api/scenario
{"material": "Aramid fabric (Nomex)", "mission": "mars", "flow_cm_s": 5}
```
If `mission` is given, the backend fills gravity, O₂ and pressure from the mission preset. For custom conditions send
`"mission": null` with `gravity_g`, `o2_pct`, `pressure_kpa`.

Response (trimmed):
```json
{
  "scenario": {"material": "Aramid fabric (Nomex)", "gravity_g": 0.38, "o2_pct": 34.0, "pressure_kpa": 56.5, "flow_cm_s": 5.0},
  "verdict": "Insufficient validated experimental evidence",
  "evidence_status": "exploratory", "confidence": "Low",
  "nearby_tendency": "nearby tests mostly burned",
  "nearby_burn_share_note": "Similarity-weighted share of the closest tests that burned. NOT a calibrated probability.",
  "blockers": ["No solid-material space test in the NASA PSI tables ran at 0.38 g (all are ~0 g).", "..."],
  "flags": ["Some nearby outcomes are inferred from NASA notes ...", "..."],
  "evidence": [{"test_id": "BASS-II-F1", "investigation": "BASS-II", "material": "Nomex natural (nomex III)",
                "o2_pct": 22.2, "flow_cm_s": 9.5, "outcome": "Burned", "outcome_basis": "inferred",
                "pressure_status": "assumed (ISS cabin; not in NASA table)", "distance": 7.68, "biggest_difference": "o2 pct",
                "source_file": "data/raw/psi/PSI-25_BASS-II/Experimental table/PSI-25_Experimental table_BASS-II.csv",
                "source_row": "24", "psi_url": "https://psi.nasa.gov/physci/repo/data/investigations/PSI-25"}],
  "why_untested": [{"topic": "gravity", "text": "...", "source_url": "https://psi.nasa.gov/..."}],
  "atmosphere_evidence": [{"kind": "gas flame", "test_id": "CFIG-N-21153F1", "o2_pct": 34.08, "pressure_kpa": 50.7,
                           "outcome": "Extinction", "test_end_raw": "SE", "burn_time_s": 44.0, "psi_url": "..."}]
}
```

## 4.4 How the website is served by the same server

- After `npm run build`, the React app is a folder of static files in `frontend-app/dist/`.
- `app.py` mounts `/assets` (JS/CSS) and a **catch-all route** that returns `index.html` for any non-API path, so links like
  `/scenario?mission=mars` work when opened directly (single-page app routing).
- API routes are registered **before** the catch-all, so `/api/*` and `/docs` always win. Unknown `/api/...` paths return a JSON 404.
- `/lite` redirects to `/lite/`, which serves `frontend/` as static files.
- If the React build is missing, `/` shows a short page telling you to run `npm run build`.

## 4.5 Errors and safety
- Request bodies are validated by Pydantic (`Scenario`, `ParseIn` models); wrong types → HTTP 422 with details.
- Unknown material or investigation IDs → 404 with a helpful message.
- CORS is open (`*`) so the dev server on port 5173 can call the API during development.
- No secrets, no external network calls, no API keys.

## 4.6 Where to add things
- New endpoint: add a function in `app.py` reading a Gold/Silver table with `_rows("gold/...")`, add it to the table in this
  chapter, add a test in `tests/test_pipeline_and_api.py`.
- New logic: put it in `engine.py`, keep the "never a probability" and "never mix experiment kinds" rules.
