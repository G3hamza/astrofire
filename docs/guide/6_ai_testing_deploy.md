# 6. AI, testing, quality and deployment

## 6.1 AI: what exists today

**🧒 Simple version.** You can type a sentence like *"Nomex on Mars at 34% oxygen and 8.2 psi"* and AstroFire fills in the form for
you. Today this is done by **simple word rules**, not a real AI model. Your teammate's chatbot will replace it later, using the same
"plug" (API).

**🛠️ Engineer version.**
- File: `backend/scenario_parse.py`, endpoint `POST /api/scenario/parse` with body `{"text": "..."}`.
- It uses **regular expressions** to find:
  - **material** (aliases: nomex/aramid, acrylic/plexiglass/PMMA, SIBAL/cotton-fiberglass, ultem, silicone, wax; plus a list of
    common materials NASA never tested, like Kevlar or nylon, which get an honest warning);
  - **mission** (mars/martian, moon/lunar/artemis, exploration/gateway/orion/8.2 psi, ISS/station/orbit);
  - **oxygen** ("34% oxygen", "O2 30%");
  - **pressure** with unit conversion (kPa, hPa, mbar, psi/psia ×6.89476, atm ×101.325, bar ×100);
  - **gravity** ("0.38 g", "1/6 g", "microgravity", "Earth gravity");
  - **air flow** (cm/s, mm/s, m/s; "still air" = 0).
- Output contract (what the chatbot must also produce):
  ```json
  {"scenario": {"material": "Aramid fabric (Nomex)", "mission": "mars", "gravity_g": 0.38, "o2_pct": 34.0, "pressure_kpa": 56.5, "flow_cm_s": 5.0},
   "understood": [{"field": "o2_pct", "value": 34.0, "text": "34% oxygen"}],
   "defaulted":  [{"field": "flow_cm_s", "value": 5.0, "reason": "not in the text; typical cabin ventilation used by NASA tests"}],
   "warnings":   []}
  ```
- If numbers match a mission preset (34% / 56.5 kPa on Mars), the mission is kept; if they differ, it becomes a custom scenario.
- **How the chatbot plugs in:** either call `/api/scenario/parse` with the user's text, or produce the same JSON itself and call
  `POST /api/scenario` with the `scenario` object. Show the user what was understood and what was defaulted.

## 6.2 AI: what was removed and why
- **Ask NASA** (search 307 NASA papers + Claude-written answers with citations) and its **RAG** search index were **removed**, because
  the NTRS papers are not on the challenge resources page.
- No LLM, no API key and no external AI call remain in the app. The `anthropic` package was removed from `requirements.txt`.
- **No machine-learning prediction model** is used. `data/gold/ml/` holds an earlier, **unvalidated** feature table; don't present it.

## 6.3 Testing

**🧒 Simple version.** Tests are small programs that check the app still does the right thing after every change, like a checklist
a robot runs in 3 seconds.

**🛠️ Engineer version.** `pytest -q` runs **40 tests** (after `python -m pipelines.orchestration.run_all`):

| File | Checks |
|---|---|
| `tests/test_pipeline_and_api.py` | Data rules (no shape-only PMMA, inferred never "reliable", every Gold row traceable to a real file), Moon → Insufficient + gravity explanation, all endpoints respond, removed endpoints are 404 |
| `tests/test_demo_flow.py` | The demo script works: 263 tests; ISS Nomex evidence with PSI links; Mars Nomex Insufficient with 3 reasons and a gas flame near 34%; Moon/Mars cells have no solid tests; 24 investigations |
| `tests/test_evidence_context.py` | "Why untested" topics per mission; flames never in the evidence table; CFI loaded once without invented outcomes; FLEX-2 is a matrix; ACME outcomes only from NASA SE/FT codes; session logs are not tests; all 24 investigations loaded; no paper data in scenarios; free-text parser cases |
| `tests/test_frontend.py` | Every page route serves the app; API not shadowed; **no "probability / % chance / predict" wording** anywhere in the UI code; `/lite/` served, redirect works, no external scripts |

The data pipeline has its own **47 validation checks** (chapter 2.7).

## 6.4 Continuous integration (CI)
`.github/workflows/ci.yml` runs on every push to GitHub: install Python packages → check the folder structure → compile → run the
pipeline + validation → **build the React app** → run pytest → warn if regenerated data differs from the committed data → upload the
quality report. **Status:** written, but not run yet (no GitHub repo).

## 6.5 Deployment

**🧒 Simple version.** "Deploying" means putting the app on a computer on the internet, so judges can open a link instead of running
it on your laptop.

**🛠️ Engineer version.**
- **Dockerfile** (multi-stage):
  1. `node:20-slim` installs and builds the React app;
  2. `python:3.12-slim` installs Python packages, copies the project and the built app, runs the pipeline;
  3. starts `uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000}`.
- `.dockerignore` keeps out `.venv`, `node_modules`, `dist`, `.git`, notebooks.
- **Render** (`render.yaml`): one Docker web service, free plan, health check `/api/stats`, **no secrets needed**.
- **Status:** not deployed; the Dockerfile has not been test-built (no Docker on this laptop). GitHub is blocked on this network by a
  certificate-revocation check (see the main chat / `README`).

## 6.6 Quality rules (non-functional requirements)

| Rule | How it's enforced |
|---|---|
| Honesty (no probability) | Engine returns counts + a "NOT a calibrated probability" note; UI test scans for forbidden words |
| Traceability | Every evidence row has PSI URL + file + row; Gold rows tested to point at real files |
| Performance | All API calls 4–15 ms locally (measured) |
| Reliability | Works offline; error states with retry; `/lite/` backup |
| Usability | Checked at 1366×768 and 375 px; SRS-ordered Scenario page |
| Accessibility | Icons + words + shapes, colorblind-checked colors, keyboard focus, table views |
| Security | No secrets, no external calls; inputs validated by Pydantic |
| Maintainability | Website only talks to `/api/*`; typed client |
| Quality gate | Pipeline (47 checks) + 40 tests before each commit |
