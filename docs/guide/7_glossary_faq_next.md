# 7. Glossary, FAQ and what to improve next

## 7.1 Glossary

| Term | Meaning |
|---|---|
| **PSI** | NASA Physical Sciences Informatics: the online archive of space experiment data. Our only data source |
| **Investigation** | One NASA experiment program (e.g. BASS-II), with an ID like PSI-25 |
| **ISS** | International Space Station (~0 g, ~21% O₂, ~101 kPa) |
| **Cygnus** | Uncrewed cargo spacecraft; SAFFIRE fires ran inside it after it left the ISS |
| **CIR / MSG** | Combustion Integrated Rack / Microgravity Science Glovebox: ISS lab hardware where fires are run safely |
| **Microgravity (~0 g)** | Near-weightlessness in orbit; no buoyant airflow |
| **Partial gravity** | Moon 0.166 g, Mars 0.38 g |
| **Exploration atmosphere** | 34% O₂ at 56.5 kPa (8.2 psia), planned for Moon/Mars habitats |
| **kPa / psia / atm / bar** | Pressure units: 101.3 kPa = 14.7 psia = 1 atm = 1.013 bar |
| **% O₂** | Oxygen share of the air by volume (Earth 21%) |
| **Air flow (cm/s)** | How fast air moves past the sample; in space it replaces buoyancy |
| **Opposed / concurrent flow** | Air against / with the flame's spread direction |
| **PMMA** | Acrylic plastic (Plexiglas), NASA's reference material |
| **Nomex** | Fire-resistant aramid fabric used in suits and covers |
| **SIBAL** | Cotton-fiberglass fabric used in SAFFIRE |
| **Burned / Went out / Blowoff / No ignition** | Test outcomes (chapter 1.6) |
| **SE / FT** | ACME codes: self-extinguished / flow terminated while still burning |
| **Disruption** | FLEX: the burning droplet broke apart |
| **Observed / Inferred / Assumed / Not recorded** | NASA wrote it / we derived it from NASA's notes / a stated assumption / NASA didn't record it |
| **Bronze / Silver / Gold** | Raw files / clean per-experiment tables / analysis tables the app reads |
| **Quarantine** | Where bad or duplicate rows are stored with the reason; nothing is deleted |
| **Blocker** | A reason NASA's data can't answer a scenario |
| **Flag** | A warning about evidence quality that doesn't block |
| **Evidence distance** | How different the closest test is (chapter 3.2); smaller = closer |
| **Atmosphere evidence** | Closest droplet/gas flames at the same O₂ and pressure; never a verdict input |
| **NASA-STD-6001 Test 1** | NASA's Earth-based upward flammability test; results in MAPTIS (not in our data) |
| **SPA** | Single-page app: one web page that changes views without reloading |
| **API / endpoint** | A URL the website calls to get data (e.g. `/api/gaps`) |
| **CI** | Continuous integration: tests that run automatically on every push |

## 7.2 FAQ

**Why does Mars always say "Insufficient validated experimental evidence"?**
Because no solid material in NASA's PSI data was ever burned at Mars gravity, at 34% O₂, or at 56.5 kPa. StarryNight refuses to guess
outside tested conditions. That's the finding: it shows where NASA needs to test.

**Why not just download the 255 GB?**
Those are videos and photos of the same tests already in the tables. They add no new conditions.

**Why show gas and droplet flames if they're not materials?**
They're the closest real space flames to the habitat atmosphere (e.g. ACME at 34.08% O₂ / 50.7 kPa). They show how flames behave in
that air, so they're useful context, but they never change a verdict.

**What does "inferred" mean on a BASS-II test?**
NASA's note listed only air flows and never wrote "went out", so we infer it kept burning. It's badged so nobody treats it as proven.

**Why is pressure "assumed" for ISS tests?**
The PSI tables don't record it. ISS cabin pressure is ~101.3 kPa, so we use that and label it.

**Why did Ask NASA disappear?**
It used NASA technical papers (NTRS), which aren't on the challenge resources page. The team decided to use only the challenge data.

**Is there any AI?**
Only a rule-based text parser for "describe your scenario". The team chatbot will plug into it (chapter 6.1).

**Where do I change the verdict rules?**
`backend/engine.py → scenario()`; then run `pytest -q` (chapter 3.12).

## 7.3 What to improve next (ideas for the team)

| Area | Idea | Effort |
|---|---|---|
| Deploy | Push to GitHub, get CI green, deploy on Render, add the live link to README | Small (needs network fix) |
| AI | Connect the chatbot to `/api/scenario/parse`; show "understood / defaulted" like today | Medium |
| Data | Process SAME/SAME-R raw particle files from PSI (in Google Colab) to show real smoke results per material | Medium |
| Data | Extract flame spread rates from BASS-II videos (PSI raw data) to add a measured quantity, not just outcomes | Large |
| Engine | Weight observed outcomes more than inferred ones; let users see the distance scales and change them | Small |
| Engine | Show the evidence for a material across all missions in one view (a "material report") | Medium |
| UI | Projector test; outsider "understand Home in 10 seconds" test; refresh the team brief and the project-map artifact | Small |
| Demo | Record the 2-minute video; rehearse 3 times; prepare the submission text and deck | Small |
