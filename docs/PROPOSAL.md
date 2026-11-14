# AstroFire — Project Proposal

**NASA Space Apps Cairo 2026 · Challenge: Flame in Freefall · Team Starry Night**
Live project: https://astrofire.vercel.app · Code: https://github.com/G3hamza/astrofire

---

## 1. Summary
AstroFire is an evidence-first fire-safety analyst for spacecraft, the ISS, Moon and Mars bases and pressurized rovers.
It turns NASA's Physical Sciences Informatics (PSI) combustion experiments into clear answers to three questions:
**Will it burn? What proves it? How sure are we?** Every answer links to the exact NASA test record behind it, and when
NASA has never tested a case, AstroFire says so plainly: *"Insufficient validated experimental evidence."*

## 2. The problem
Fire behaves differently in space. Without gravity, hot gas does not rise, so flames depend on air flow and slow
diffusion of oxygen. NASA has flown many combustion experiments on the ISS and the Cygnus spacecraft, but the results
sit in 24 separate investigations with different file formats, columns and conventions.

At the same time, Artemis-era habitats are planned at an **"exploration atmosphere"** of about **34% oxygen at 56.5 kPa**
(the challenge range is ≥ 30% O₂ at ≤ 70.3 kPa), so crews can begin spacewalks faster. Higher oxygen makes cabin
materials ignite and burn more easily, and a fire in a sealed habitat is among the most serious crew hazards (Apollo 1,
the Mir fire, Apollo 13).

AstroFire's analysis of the PSI data found the central gap: **NASA's 263 solid-material space fire tests all ran at
13.6–22.2% oxygen, about 0 g and normal cabin pressure. No solid cabin material in PSI has been burned at Moon/Mars
atmosphere or at Moon (0.166 g) or Mars (0.38 g) gravity.** Designers today cannot easily see what is known, what is
not, and which experiments matter most for their habitat.

## 3. Who benefits
- **Habitat and spacecraft engineers** choosing cabin materials and atmospheres.
- **Researchers and mission planners** deciding which experiments to run next (e.g. NASA's upcoming partial-gravity work).
- **Fire-safety equipment designers** working on smoke detection and suppression for spacecraft.
- **Students and educators** learning space combustion from real data.
- **Earth**: the same research improves smoke detectors, firefighter equipment and fire safety in confined spaces
  (mines, submarines, aircraft).

## 4. The solution
A web application with an AI analyst, built only on NASA data:

| Feature | What it does | Challenge objective |
|---|---|---|
| **Scenario check** | Pick a material and place (ISS, Moon, Mars) or set oxygen, pressure, gravity and air flow, or describe it in words. Returns a rule-based verdict, the closest NASA tests, blockers and flags | Interpret investigations for habitat conditions |
| **Gravity bounds** | Uses NASA's 0 g results and Saffire-II's 1 g comparison as the two ends around Moon/Mars gravity, and states when they do not cover a case | "Micro- and normal-gravity results could bound partial gravity" |
| **AI analyst (Ask)** | Answers questions in plain language from NASA evidence only, with clickable citations; also understands Arabic questions | AI dashboard that summarizes and interprets |
| **Habitat ranking** | Scores all 24 investigations 0–100 for a spacecraft, the ISS, a Moon base, a rover or a Mars base, with explained score parts | Identify the most relevant investigations |
| **Investigation profiles & compare** | Objective, fuels, sample size, oxygen, air flow, what varied, sensors; side-by-side comparison | Similarities and differences between investigations |
| **Gaps map** | Gravity × oxygen × pressure grid of what was and was not tested | Show knowledge gaps |
| **Apply** | 8 clean downloadable datasets for flammability modeling, research insights for detection / suppression / materials, and Earth applications | Data for modeling; next-generation equipment; Earth benefits |

## 5. How it works
1. **Data pipeline (Bronze → Silver → Gold).** The original PSI files are kept unchanged with SHA-256 fingerprints.
   Each investigation is cleaned into its own table; every row keeps its NASA source file and row number. Suspicious
   rows go to a quarantine table with the reason — nothing is deleted. Gold tables feed the app, the datasets and the
   AI knowledge base.
2. **Honest labels.** Each outcome is marked *observed* (NASA recorded it), *inferred* (derived from NASA's notes) or
   *not recorded*. ISS/Cygnus solid-test pressure is marked *assumed*.
3. **Verdict engine.** A deterministic rule engine measures the "evidence distance" from a scenario to every NASA test,
   takes the closest ones, checks blockers (untested gravity, oxygen or pressure) and reports what happened nearby.
   Verdicts never come from the AI.
4. **AI analyst.** Rules detect the question type and entities; tools gather evidence from the engines and a 234-passage
   NASA knowledge base (BM25 search); a language model (open-weight gpt-oss-120b on Groq, with fallbacks) writes the
   answer from that evidence. Guardrails reject any probability wording, any number not in the evidence, any citation
   that does not exist, and any attempt to change a verdict. If the model fails or is unavailable, a template answer
   from the same NASA records is shown.
5. **Delivery.** FastAPI backend and React/TypeScript frontend, deployed on Vercel; CI on GitHub Actions; a Docker
   image is also published.

## 6. Validity and results
- **139 automated tests**: data rules, every API endpoint, every screen, full user journeys, input limits, error
  handling, security headers, secrets, AI guardrails, ranking and gravity bounds.
- **AI evaluation (26 questions)**: 100% correct refusals of off-topic questions, 100% correct "insufficient evidence"
  answers, 0 probability violations, 96% citation accuracy; 83% fact accuracy with the live model and 100% in template mode.
- **Traceability**: every number on screen can be followed to a NASA file and row or PSI page.
- **Key result**: the app shows quantitatively that the habitat atmosphere and partial gravity are untested for solid
  materials, and which existing investigations (e.g. FLEX and ACME for oxygen/pressure ranges) come closest.

## 7. What is new
- **Refusing to guess is a feature**: the system is designed to stop at the edge of the evidence and explain why.
- **Gravity bounds** from existing 0 g and 1 g data instead of an unsupported extrapolation.
- **An AI that cannot invent**: it only rewrites evidence chosen by deterministic code, and every sentence is checked.
- **Habitat-specific relevance ranking** with transparent scoring, across all 24 PSI combustion investigations.

## 8. Feasibility and next steps
The full system is built, deployed and free to run (Vercel free tier, free Groq tier, public-domain data). Next steps:
1. Add new PSI data when NASA's partial-gravity experiments (e.g. LUCI, FM2) publish results — the pipeline is designed
   to take a new investigation with a parser and a curation row.
2. Material shortlist builder and exportable evidence reports for design reviews.
3. Answers fully in Arabic and other languages.
4. Validation with NASA fire-safety engineers and university combustion labs.

## 9. NASA data and resources
- NASA Physical Sciences Informatics (PSI) — 24 combustion investigations including BASS, BASS-II, Saffire-I/II/III,
  SAME, SAME-R, FLEX, CFI, ACME, E-FIELD Flames — public domain (CC0). https://psi.nasa.gov
- Resources listed on the Space Apps "Flame in Freefall" challenge page (NASA spinoffs and background).

## 10. Use of AI (disclosure)
- **In the product**: an open-weight language model (openai/gpt-oss-120b via Groq, fallbacks qwen3.8-27b and gpt-oss-20b)
  writes answer text only from NASA evidence selected by AstroFire's code; it cannot add facts, numbers or verdicts, and
  every answer states whether it was AI-written or a template.
- **In development**: the team used AI coding assistants (Anthropic Claude) to help write and review code, tests and
  documentation. The team made the design decisions, set the data rules and reviewed the results.
- **Not AI**: the data pipeline, verdict engine, gravity bounds and ranking are deterministic and reproducible.

## 11. Links
- Project: https://astrofire.vercel.app (backup version: /lite/, API: /docs)
- Repository: https://github.com/G3hamza/astrofire
- Handbook: `docs/HANDBOOK.md` · Technical context: `docs/CONTEXT.md` · Demo script: `docs/DEMO_SCRIPT.md`
