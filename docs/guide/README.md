# The StarryNight Guide — start here

This guide explains **everything** in the StarryNight prototype: the science behind it, the NASA data, how the data is cleaned,
how answers are calculated, the backend, the website, the "AI" part, testing and deployment.

Every chapter is written in two layers:

- **🧒 Simple version** — the idea in plain words. If you're new, read only these first.
- **🛠️ Engineer version** — the exact rules, files, numbers and code paths, so you can change things safely.

## The whole project in one minute (simple version)

People are planning homes on the Moon and Mars. Inside, the air will be different from Earth: **more oxygen (34% instead of 21%)
and lower pressure**, and gravity will be weaker. Fire behaves differently in all of those conditions.

NASA has done hundreds of real fire experiments in space and published the results in an online library called **PSI**.
StarryNight reads all of that data and lets you ask: *"If this material catches fire in this habitat, will it keep burning?"*

It answers with what NASA's tests actually show, links to the exact test that proves it, and, very importantly, **says honestly when
NASA never tested those conditions**. That honesty is the point: it shows NASA where to test next.

## How the parts fit together

```
 1. NASA PSI files            2. Pipeline (Python)             3. Engine + API (Python)        4. Website (React)
 ─────────────────            ───────────────────────          ───────────────────────         ──────────────────
 24 experiment folders  ──►   clean, check, organize   ──►     find closest tests,     ──►     screens, charts,
 (CSV tables)                 Bronze → Silver → Gold           decide verdict, explain         links to NASA
 data/raw/psi/                pipelines/                       backend/                        frontend-app/ (+ frontend/ lite)
```

## Chapters

| # | Chapter | What you'll learn |
|---|---|---|
| 1 | [Domain knowledge: fire in space](1_domain_space_fire.md) | Why fire is different in space, oxygen, pressure, gravity, flammability tests, the habitat atmosphere |
| 2 | [The NASA data and the pipeline](2_data_and_pipeline.md) | All 24 investigations, what each measured, Bronze/Silver/Gold, cleaning rules, quality checks, data fixes |
| 3 | [The engine: how answers are calculated](3_engine_and_analysis.md) | Distance, verdicts, blockers, confidence, "why untested", atmosphere evidence, gaps map |
| 4 | [Backend and API](4_backend_api.md) | FastAPI, every endpoint, request/response shapes, how the website is served |
| 5 | [Frontend and UI](5_frontend_ui.md) | React, Vite, TypeScript, Tailwind, Recharts, every screen, design system, accessibility |
| 6 | [AI, testing, quality and deployment](6_ai_testing_deploy.md) | The scenario parser, what was removed, tests, CI, Docker, Render |
| 7 | [Glossary, FAQ and what to improve next](7_glossary_faq_next.md) | Every term, common questions, enhancement ideas |

## Run it yourself

```bash
pip install -r requirements.txt
python -m pipelines.orchestration.run_all        # build + check the data (~30 s)
pytest -q                                        # 40 tests
cd frontend-app && npm install --legacy-peer-deps && npm run build && cd ..
uvicorn backend.app:app                          # open http://127.0.0.1:8000/
```

Backup version without the React build: http://127.0.0.1:8000/lite/ · API documentation: http://127.0.0.1:8000/docs

## The five rules the whole project follows

1. **Never invent a number.** Every number comes from a NASA file. If it's missing, the app says "not available".
2. **Never show a probability.** No "% chance". We show counts like "2 of 5 closest tests burned".
3. **Every claim links to its source.** NASA PSI page, and the exact file and row.
4. **Label weak data.** Each value is *observed* (NASA wrote it), *inferred* (we derived it from NASA's notes) or *assumed*.
5. **Only the data the challenge gave us.** The PSI combustion repository and the NASA pages on the challenge resources tab.
