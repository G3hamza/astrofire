# The StarryNight Handbook

**For young engineers (and anyone new): how to use StarryNight, how to read what it tells you, how to apply it, and how
it works inside.** Plain words first, then the technical details. No step is skipped.

Open it here: **https://astrofire.vercel.app**

---

## Part 1 — The big idea in five minutes

### 1.1 Why fire in space is different
On Earth, a flame heats air, hot air is lighter, so it rises and fresh air (with oxygen) flows in from below. That is
why a candle flame is a tall teardrop. In space there is no "up": hot air does not rise (no **buoyancy**). A candle flame
becomes a small blue ball that gets oxygen only slowly, by **diffusion**. So in space:
- **Air flow matters a lot.** A fan or ventilation can feed a fire that would otherwise starve.
- **Oxygen matters a lot.** More oxygen in the air = materials catch fire more easily and burn faster.
- Earth fire tests do not tell you everything about space fires.

### 1.2 Why it matters now
Astronauts are going back to the Moon and then to Mars. Moon bases and rovers will use **more oxygen (about 34 %)
at lower pressure (about 56.5 kPa)** than Earth air (21 % at 101 kPa), so astronauts can put on spacesuits faster.
More oxygen makes cabin materials (fabrics, plastics) much easier to burn. History shows how dangerous fire is in
spacecraft: Apollo 1 (1967), the Mir station fire (1997), Apollo 13's oxygen tank (1970).

### 1.3 What NASA has
NASA ran fire experiments on the International Space Station (ISS) and on the Cygnus cargo spacecraft and published
the results in a database called **PSI** (Physical Sciences Informatics). There are **24 combustion investigations**:
burning solids (BASS, BASS-II, Saffire), smoke from overheated materials (SAME, SAME-R), burning fuel droplets (FLEX,
CFI), gas flames (ACME), and more.

### 1.4 What StarryNight does
StarryNight reads all that NASA data and answers your questions, **always showing the NASA test that proves the answer**.
If NASA never tested something, StarryNight says so: **"Insufficient validated experimental evidence."**

### 1.5 The one fact to remember
NASA burned **263 solid materials in space**, all at **13.6–22.2 % oxygen**, at **~0 g** (weightless), at normal
cabin pressure. **Nobody has burned a cabin material at Moon/Mars air or Moon/Mars gravity.** That is the gap.

---

## Part 2 — How to use StarryNight (screen by screen)

The menu is at the top. On every page there is an **Ask AI** button at the bottom right.

| Screen | What you do there | Try this |
|---|---|---|
| **Home** `/` | See the headline gap, the closest real space flames to habitat air, and why it matters. Type a question in the **Ask StarryNight** box. | Click "Would Nomex burn at 30% oxygen and 71 kPa on the Moon?" |
| **Scenario** `/scenario` | Pick a material and a place (ISS, Exploration, Moon, Mars) or move the sliders (oxygen, pressure, gravity, air flow). Or **type it in your own words**. Get a verdict and the proof. | Material Nomex, mission Mars |
| **Compare** `/compare` | Put 2–4 scenarios side by side. | ISS vs Moon vs Mars for Nomex |
| **Gaps** `/gaps` | A grid of gravity × oxygen × pressure: which boxes NASA tested, which have only flames of other fuels, which were never tested. | Find the Moon/Mars pins |
| **Charts** `/charts` | The flammability map: oxygen vs air flow, each dot a NASA test, colored by outcome. | Filter by material |
| **Ask** `/ask` | Chat with the AI analyst. It answers only from NASA data and cites every fact. | "How do SAME and SAME-R differ?" |
| **Rank** `/rank` | Choose a habitat (spacecraft, ISS, Moon base, rover, Mars base); see the 24 investigations ranked by relevance, with reasons. | Pressurized lunar rover |
| **Investigations** `/investigations` | One card per NASA investigation: goal, fuels, conditions, what changed between tests, sensors. Tick 2–6 to compare. | Tick BASS and BASS-II |
| **Experiments** `/experiments` | All 24 investigations with charts (FLEX, CFI, ACME, smoke). | Open ACME |
| **Materials** `/materials` | Every material: named by NASA or unknown, how many tests. | Open a PMMA material |
| **Apply** `/applications` | Download data for modeling; what the research means for detectors, extinguishers, materials; fire safety on Earth. | Download `solid_fire_tests` |
| **Quality** `/data` | How trustworthy the data is: observed vs inferred vs missing. | Read the outcome basis bar |
| `/lite/` | A simple backup version if the main app fails. | — |
| `/docs` | The technical API (for programmers). | — |

### 2.1 Asking good questions
- Name the **material** (Nomex, PMMA/acrylic, SIBAL cotton-fiberglass, silicone, Ultem…), the **place** (ISS, Moon,
  Mars, rover, spacecraft) and, if you know them, **oxygen %** and **pressure** (kPa, psi or atm all work).
- Name **investigations** by their short names: BASS-II, SAME-R, FLEX, Saffire-II, ACME CFI-G, E-FIELD.
- Follow-ups work: after "Summarize FLEX", ask "What did it vary between tests?".
- Greetings and "what can you do?" get an introduction. Off-topic questions (pizza, rocket propellant) get
  "No data in the NASA papers provided." — on purpose.

---

## Part 3 — How to read what StarryNight tells you

### 3.1 The four verdicts (Scenario and AI)
| Verdict | Meaning |
|---|---|
| **Evidence suggests it burns** | The closest NASA tests near your conditions mostly burned |
| **Borderline in tested evidence** | Nearby tests are mixed |
| **Evidence suggests it goes out** | Nearby tests mostly went out |
| **Insufficient validated experimental evidence** | NASA never tested close enough to your conditions. StarryNight will not guess |

The verdict comes from fixed rules (the "rule engine"), **never from the AI**. The AI only explains it.

### 3.2 Coverage words (AI scenario answers)
**Directly tested** (NASA tested this material near these conditions) · **Closest evidence** (only nearby tests) ·
**Gap** (something important — gravity, oxygen or pressure — was never tested).

### 3.3 Blockers and flags
- **Blockers** say *why* the evidence is insufficient (e.g. "No solid-material space test ran at 0.38 g").
- **Flags** are warnings that do not block (e.g. "some outcomes are inferred", "pressure assumed").

### 3.4 Observed, inferred, not recorded (very important)
- **observed** — NASA wrote down what happened (e.g. "Extinction"). This is real ground truth.
- **inferred** — NASA did not write the outcome; it was worked out from NASA's notes. Less certain.
- **not_recorded** — nobody knows the outcome.
Of 263 solid tests: 39 observed, 101 inferred, 123 not recorded.

### 3.5 Assumed pressure
NASA's tables for the ISS/Cygnus solid tests do not record pressure. StarryNight uses the normal cabin pressure
(~101.3 kPa) and marks it **assumed**. FLEX droplet tests have **measured** pressure.

### 3.6 Evidence and citations
- A table row shows the NASA test id, material, oxygen, pressure, air flow, outcome and a **file#row** chip — the exact
  line in NASA's file — plus a link to the PSI page.
- In AI answers, **[E1], [E2]…** are clickable: they open the evidence (record, file, row, link).
- **NASA findings** = facts from NASA. **StarryNight interpretation** = our reading, clearly labelled. **Limits and gaps** =
  what is missing or uncertain.

### 3.7 Colors
Burned = orange · went out = blue · blowoff = magenta · not recorded = grey · insufficient evidence / blockers = red ·
flags, borderline, inferred = amber · observed = green. Colors always come with an icon and text.

### 3.8 Moon/Mars gravity bounds
NASA has no tests at Moon or Mars gravity. StarryNight shows the two ends it does have:
- **0 g**: what happened in space (microgravity) for that material.
- **1 g**: NASA's own normal-gravity comparison in Saffire-II (burn length on Earth vs in space).
If both ends were measured at *your* oxygen and pressure, they **bracket** your case (the value in between is still
untested). If not (e.g. Moon air), StarryNight says the bounds **do not cover** your scenario. **E-FIELD Flames** only
*mimicked* partial gravity with an electric field (gas flames). **LUCI** and **FM2** are future partial-gravity data.

### 3.9 Ranking scores
0–100 = conditions (40) + relevance (25) + fuel (20) + evidence (15). Click a row to see each part and the reasons.
It means "how relevant is this NASA work to my habitat", **not** "how safe" or "how likely to burn".

### 3.10 Footer of an AI answer
"Written by openai/gpt-oss-120b from the evidence" = a real AI wrote it from NASA evidence. "Template answer from NASA
records (not AI-written)" = the AI was busy or not needed; the facts are the same, the wording is simpler.

---

## Part 4 — How to apply it (what an engineer does with the answers)

1. **Material choice for a habitat**: run Scenario for each candidate material at your habitat atmosphere. If the
   verdict is "Insufficient…", that material needs new testing before you rely on it. Use the closest evidence to
   decide *which* tests to request (oxygen, pressure, gravity, air flow).
2. **Planning experiments**: open Gaps and Rank for your habitat; the red, never-tested cells at high oxygen/low
   pressure are where new tests (LUCI, FM2, ground tests) add the most knowledge.
3. **Detectors**: Apply → Detection: SAME/SAME-R smoke particle data is NASA's reference for designing and evaluating
   spacecraft smoke detectors.
4. **Suppression**: Apply → Suppression: FLEX measured how CO₂ and helium dilution put flames out (for liquid-fuel
   droplets — not solid materials).
5. **Modeling**: Apply → Data: download the CSVs. Read each caveat. Use only `observed` outcomes as labels; do not
   impute missing values; the ML table is too small to make predictions and is **not validated**.
6. **Reporting**: always copy the citation (investigation id + file#row or PSI link) with any number you use.
7. **Earth**: spinoffs (smoke detector that ignores dust, firefighter air tanks and clothing, water-mist extinguishers)
   and NASA's Earth-benefit statements (mines, submarines, engines).

What **not** to do: do not read a "nearby burn share" as a probability; do not treat interpretation as a NASA result; do
not use 0 g results as Moon/Mars results; do not present inferred outcomes as observed.

---

## Part 5 — How it works inside (technical, step by step)

### 5.1 The data pipeline (Bronze → Silver → Gold)
1. **Bronze** — NASA's original PSI files in `data/raw/psi/` (never edited). Each gets a fingerprint (SHA-256) and source
   URL in `data/manifests/bronze_manifest.csv`.
2. **Silver** — `pipelines/transformation/silver.py` cleans each investigation into its own table
   (`data/silver/investigations/*.csv`), plus materials, samples, properties and long-format measurements. Each row keeps
   `source_file`, `source_row` and the original row. Bad rows go to `data/quarantine/quarantine.csv` with the reason —
   nothing is deleted.
3. **Gold** — `gold.py` builds analysis tables (solid tests, droplets, gas flames, smoke…), Power BI tables, the ML
   table; `profiles.py` builds the 24 investigation profiles; `rag.py` builds the AI knowledge base.
4. **Validation** — `pipelines/validation/validate.py` checks raw files, every table (columns, types, ranges, duplicates), links between tables and the PSI-only knowledge base, and writes the quality and
   provenance reports; `dictionary.py` writes the data dictionary.
Command: `python -m pipelines.orchestration.run_all`.

### 5.2 The scenario engine (`backend/engine.py`)
Measures an "evidence distance" from your scenario to every solid test (differences scaled: 0.1 g, 2 % O₂, 15 kPa,
5 cm/s; +1.5 for a different material), takes the 8 closest, checks blockers, then reads what happened in the closest
tests. Adds closest flames at the same atmosphere (FLEX, CFI, ACME), "why untested" explanations and gravity bounds.

### 5.3 Ranking (`backend/ranking.py`)
Scores each investigation against a habitat with the four weighted parts in Part 3.9; every number is explained.

### 5.4 The AI analyst (`ai/`)
1. **Understand**: rules find the intent (scenario, rank, compare, summary, gaps, datasets, Earth, equipment, about,
   off-topic) and the entities (material, habitat, O₂, pressure, investigations), using the last 6 messages.
2. **Gather evidence** with tools that call the engines above and the knowledge base (234 passages of NASA text and
   computed summaries, searched with BM25).
3. **Write**: a template answer is built from the evidence; if the AI is available, it rewrites it (one call).
4. **Check** (guardrails): no probability words, every number must be in the evidence, every [E#] must exist, verdicts
   can't be changed, injected instructions are removed, keys are never shown. If the AI fails a check twice, the
   template answer is used.
5. **Models**: Groq `openai/gpt-oss-120b`; if busy → `qwen/qwen3.8-27b` → `openai/gpt-oss-20b` → template.

### 5.5 The website
React app (`frontend-app/`) built with Vite and Tailwind; it only talks to the API (`/api/*`). FastAPI serves the built
app, the API and the `/lite` backup from one place. On Vercel the same FastAPI app runs as a serverless function.

### 5.6 Tests
138 automatic tests (`pytest -q`): data rules, API, every screen, the demo script, user journeys, input limits, errors,
secrets, AI with a fake model (offline), guardrails, ranking, bounds, applications. Plus the AI evaluation
(`python -m ai.eval.run`, 26 questions).

---

## Part 6 — Run it, change it, deploy it

```bash
# one time
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
cd frontend-app && npm install --legacy-peer-deps && npm run build && cd ..
# every time
python -m pipelines.orchestration.run_all      # rebuild data (≈30 s)
.venv\Scripts\python -m pytest -q              # 138 tests
.venv\Scripts\python -m uvicorn backend.app:app --port 8000   # http://127.0.0.1:8000
```
- **AI keys**: copy `.env.example` to `.env`, put `GROQ_API_KEY=...` after the `=` (no spaces, no quotes). Never commit `.env`.
- **Deploy** (after changes, from the repo folder): `npx vercel@65.16.0 deploy --prod`. Keys on Vercel: Project →
  Settings → Environment Variables (Production, Secret).
- **Add a new NASA investigation**: put its PSI files in `data/raw/psi/<folder>`, add it to `INVESTIGATIONS` in
  `pipelines/common.py`, add a curation row in `data/curation/investigation_curation.csv` (with a basis), add its table
  parser in `silver.py`, re-run the pipeline and tests. See `docs/PIPELINE_GUIDE.md`.

### Troubleshooting
| Problem | Fix |
|---|---|
| Page looks old | Ctrl+F5 |
| AI answers say "Template answer" | Groq is busy or out of daily quota; wait or try later — facts are the same |
| "No data in the NASA papers provided." | The question has no fire/space/NASA words; rephrase with a material, place or investigation |
| Site slow the first time | Free hosting sleeps; first load ≈ 3 s |
| `.env` not working | Must be in the `astrofire` folder, named `.env` (not `.env.txt`), with `NAME=value` lines |

---

## Part 7 — Glossary

| Word | Meaning |
|---|---|
| Microgravity (~0 g) | "Weightless", like on the ISS |
| Partial gravity | Moon 0.166 g, Mars 0.38 g |
| Buoyancy | Hot air rising; missing in space |
| Diffusion | Slow mixing of gases without wind |
| O₂ % | Share of oxygen in the air (Earth 21 %) |
| kPa / psi | Pressure units; Earth sea level 101.3 kPa = 14.7 psi |
| Flammability limit | The oxygen level below which a material stops burning |
| Extinction / blowoff | Flame goes out / flame is blown away by the air flow |
| PMMA | Acrylic plastic, NASA's reference material |
| SIBAL | Cotton-fiberglass fabric used in Saffire and BASS |
| Nomex | Fire-resistant fabric (aramid) |
| PSI | NASA's Physical Sciences Informatics data repository |
| Investigation | One NASA experiment program (e.g. BASS-II) |
| Pillar | Prevention, detection or suppression of fire |
| Bronze / Silver / Gold | Raw → cleaned → ready-to-use data |
| BM25 | A keyword search method used to find the right NASA passages |
| LLM | Large language model (the AI that writes answers) |
| Guardrail | An automatic check on the AI's answer |
| Template answer | Answer built from the evidence without the AI |
| Citation [E#] | A link from a sentence to its evidence |

## Part 8 — Practice (check yourself)
1. Run Scenario: PMMA on the ISS. What verdict, and how many nearby tests burned?
2. Change the mission to Mars. Which three blockers appear?
3. In Rank, choose "Pressurized lunar rover". Why are FLEX and ACME CFI-G at the top, not BASS-II?
4. Ask: "What did BASS-II not record?" Which factors are missing?
5. Open the bounds card for SIBAL on the Moon at 21.5 % O₂ and 101 kPa. Do the bounds cover the case? Why?
6. On Apply, download `solid_fire_tests.csv`. How many rows have `outcome_basis = observed`?
7. Ask: "What is the probability Nomex burns on Mars?" What does StarryNight do, and why?

(Answers: 1 — see the screen; 2 — gravity, oxygen, pressure; 3 — their oxygen/pressure ranges are closest to 34 % /
56.5 kPa while all solid tests are at cabin air; 4 — see the profile's "not recorded"; 5 — yes, both ends exist at cabin
air, the 0.166 g value itself is still untested; 6 — 39; 7 — it gives the verdict and evidence but never a probability.)
