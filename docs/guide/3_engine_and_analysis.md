# 3. The engine: how answers are calculated

All of this lives in **`backend/engine.py`** (class `Engine`). It is plain, explainable logic: **no machine learning, no AI,
no probabilities**. Every answer can be traced to specific NASA tests.

## 3.1 The idea

**🧒 Simple version.** You describe a situation: a material, the oxygen, the pressure, the gravity and how fast the air moves.
StarryNight looks through all 263 real space fire tests and finds the ones **most similar** to your situation, like finding the
classmates who are most like you. Then it looks at what happened in those tests: did they burn or go out? If the closest tests are
still very different from your situation (for example, nobody ever tested at Mars gravity), it refuses to guess and tells you why.

**🛠️ Engineer version.** A nearest-neighbour search in a 4-dimensional condition space (gravity, O₂, pressure, flow) with a
material-match penalty, followed by explicit **blocker** rules that override the vote when the scenario is outside the tested range.

## 3.2 Step 1: measure "how different" each test is (distance)

Each condition is divided by a **scale**: how much difference counts as "one step" (`SCALE` in `engine.py`):

| Condition | One step = |
|---|---|
| Gravity | 0.1 g |
| Oxygen | 2 percentage points |
| Pressure | 15 kPa |
| Air flow | 5 cm/s |

`distance = √( (Δgravity/0.1)² + (ΔO₂/2)² + (Δpressure/15)² + (Δflow/5)² )`, then **+1.5 if the material is different**.

**Worked example (real numbers):** Nomex on the ISS (0 g, 21% O₂, 101.3 kPa, 5 cm/s) vs test **BASS-II-F3** (Nomex, 0 g, 21.7%,
101.3 kPa, 8 cm/s):
ΔO₂ = −0.7 → −0.35 steps; Δflow = −3 → −0.6 steps; others 0 → distance = √(0.35² + 0.6²) = **0.69**, same material so no penalty.
The table shows **"differs most in: flow"** because flow was the largest of the four steps.

## 3.3 Step 2: look at what happened in the closest tests

- Only tests with recorded oxygen, flow and a known outcome are candidates (140 of the 263 have conditions).
- The **8 closest** are kept; the **5 closest** are shown in the evidence table.
- Each of the 8 gets a weight `1 / (1 + distance)` (closer = more say). The weighted share that burned gives a **tendency**:
  ≥ 0.66 "mostly burned", ≥ 0.33 "mixed", otherwise "mostly went out".
- This share is **never shown as a percentage** (SRS rule FR2.7). The UI shows a plain count instead: *"Closest tests: 2 of 5 burned"*,
  and the API sends a note: "NOT a calibrated probability".

## 3.4 Step 3: blockers (when StarryNight refuses to guess)

A **blocker** is a reason the data can't answer. Any blocker → verdict **"Insufficient validated experimental evidence"**,
status *exploratory*, confidence *Low*.

| Blocker | Rule |
|---|---|
| Gravity never tested | No solid test at this gravity (all PSI solid tests are ~0 g) |
| Oxygen out of range | O₂ more than 0.5 points outside 13.6–22.2% |
| Pressure never tested | |pressure − 101.3| > 15 kPa (all PSI solid tests are at assumed cabin pressure) |
| Material never tested here | None of the 8 closest tests is the same material |

## 3.5 Step 4: verdict and confidence

| Situation | Verdict |
|---|---|
| Any blocker | **Insufficient validated experimental evidence** |
| Tendency "mostly burned" | **Evidence suggests it burns** |
| Tendency "mixed" | **Borderline in tested evidence** |
| Tendency "mostly went out" | **Evidence suggests it goes out** |

**Confidence** (only without blockers): *High* if the best distance < 1.0 and at most one flag; *Medium* if best distance < 2.5;
otherwise *Low*.

**Flags** (amber notes) don't block but warn: some nearby outcomes are *inferred*, some samples are *not named* by NASA, pressure
is *assumed*.

### Two real results
| Scenario | Verdict | Why |
|---|---|---|
| Nomex · ISS | **Borderline**, Medium | Closest 5: 2 Nomex tests burned (inferred), 3 PMMA tests went out (observed); best distance 0.69; 3 flags |
| Nomex · Mars | **Insufficient**, Low | 3 blockers: no test at 0.38 g; 34% O₂ outside 13.6–22.2%; 56.5 kPa never tested. Best distance 7.68 |

## 3.6 Step 5: explain the gap ("why untested")

`why_untested()` adds a short explanation per blocker topic, each with a PSI link:
- **Gravity:** every PSI combustion test ran at ~0 g; nothing in orbit runs at partial gravity.
- **Oxygen:** solid tests ran at cabin air or below (BASS-II lowered O₂ with nitrogen); the ISS combustion chamber did burn droplets
  (FLEX, up to 34%) and gas flames (ACME, up to 85%), but no cabin materials.
- **Pressure:** solid-test pressure isn't recorded (cabin ~101 kPa); low-pressure flames exist only for droplets (down to 50.7 kPa)
  and gas flames (down to 43 kPa).

## 3.7 Step 6: closest space flames at the same atmosphere ("atmosphere evidence")

`atmosphere()` returns the **3 closest droplet flames** (FLEX/CFI, nitrogen-diluted only) **and the 3 closest gas flames** (ACME),
by oxygen and pressure only (`distance = √((ΔO₂/2)² + (Δpressure/15)²)`). For gas flames it prefers tests where NASA recorded how
the flame ended. These are **not materials**: they never enter the evidence table and never change the verdict. They show what real
flames did in that atmosphere. Example for the habitat air (34% / 56.5 kPa): ACME **34.08% O₂, 50.7 kPa, self-extinguished
after 44 s**; FLEX **34% O₂, 71.2 kPa, ended by disruption**.

## 3.8 The gaps map

`gaps()` makes a grid:
- **Gravity rows:** 0, 0.166, 0.38, 1.0 g
- **O₂ columns:** 14–18, 18–22.5, 22.5–26, 26–30, 30–36%
- **Pressure groups:** ~101 kPa (95–105) and exploration (50–80)

Each cell counts solid tests, plus droplet and gas flames (orbit row only), and marks mission design points. Result: only
**2 of 30** space cells have a solid-material test; 7 more have only droplet/gas flames.

## 3.9 Mission coverage (Home cards)

`pipelines/transformation/gold.py → coverage()`: solid tests "near" a mission = same gravity, O₂ within ±2 points, pressure within
±15 kPa. ISS: **62** tests nearby (18 with outcome written). Exploration, Moon, Mars: none, so the cards show the closest flame
instead of a zero.

## 3.10 Flammability map (Charts page)

`flammability_map()` returns the BASS-II points with both O₂ and flow, each with outcome and basis. The chart plots air flow (x)
against O₂ (y): circles = burned, triangles = went out, diamonds = blowoff; filled = observed, hollow = inferred. A hatched band shows
the oxygen range no solid was tested at, up to the habitat line.

## 3.11 What the engine does NOT do (by design)

- No prediction model and no probability. (An ML table exists in `data/gold/ml/` from earlier work; it was **not validated** and isn't used.)
- No extrapolation outside tested ranges: that's what blockers are for.
- No mixing of experiment kinds: droplets and gas flames never count as material evidence.

## 3.12 How to change the logic safely
1. Change `SCALE`, thresholds or blockers in `engine.py`.
2. Run `pytest -q`: tests in `tests/test_pipeline_and_api.py`, `test_demo_flow.py` and `test_evidence_context.py` pin the key
   behaviours (Mars must stay "Insufficient", ISS Nomex "Borderline", flames never in evidence, no probability wording).
3. Update this chapter and `docs/DEMO_SCRIPT.md` if a demo result changes.
