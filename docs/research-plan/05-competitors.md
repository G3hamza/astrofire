# 05 · Competitors and alternatives

| Solution | Who it serves | Strengths | Weaknesses | Gap we fill | Cost | Access | Effective |
|---|---|---|---|---|---|---|---|
| NASA-STD-6001 Test 1 + MAPTIS | Materials engineers | Official, large dataset | 1 g only; doesn't answer microgravity / partial-g | Adds space-condition risk on top | 5 | 2 | 3 |
| NASA PSI website (raw) | Researchers | Original data | Manual downloads, no cross-experiment view | One schema, ranking, explanations | 5 | 3 | 2 |
| NTRS search | Everyone | All papers | Keyword search only, no answers | Cited answers in minutes | 5 | 4 | 2 |
| General chatbots (ChatGPT, Gemini) | Everyone | Fast | No grounding, can invent safety claims | Answers only from NASA sources + confidence | 4 | 5 | 1 |
| Domain experts | Agencies | Best judgment | Scarce, slow | Scales their knowledge | 1 | 1 | 5 |
| Other Space Apps teams (e.g. [FlameAtlas](https://github.com/MahmudulHasanJoy/FlameAtlas)) | Hackathon judges | Similar RAG + map | Typically "chatbot + chart" | Evidence distance, hidden-risk list, gap map, skeptic | — | — | — |

(Scores 1–5, higher is better. Competitor scores are **[assumption]**.)

## The gap
Nobody turns microgravity results into a **decision for a specific mission**, with **how sure we are**, and flags **materials that pass Earth tests but not space**.

## Unfair advantage
- Honest confidence ("evidence distance") — most AI tools hide uncertainty.
- Team mix: AI + backend + UI + a lead with research and Lean Six Sigma (FMEA) background.
