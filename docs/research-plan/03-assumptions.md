# 03 · Assumptions map

## Known (evidence)
- Materials can burn at lower oxygen in microgravity than in normal gravity (BASS-II). → 04 #1
- Flames quenched when the ISS fan was turned off; may not hold in future high-O₂ atmospheres. → 04 #2
- NASA studied an exploration atmosphere of 8.2 psia / 34% O₂ that "may increase fire risk". → 04 #3
- Flight materials are certified with NASA-STD-6001 Test 1, in normal gravity. → 04 #4
- NASA PSI hosts combustion investigations (BASS, FLEX, SAFFIRE, SAME…). → 04 #5

## Believed (needs checking)
- Engineers would use a cited, confidence-rated tool over reading papers.
- Judges see "evidence distance" as original.
- Our simplified flammability model is acceptable if labelled as illustrative.

## Risky (could kill the demo)
| Rank | Assumption | Test it | When | Owner |
|---|---|---|---|---|
| 1 | We can download and parse PSI tables in time | Backend opens BASS-II table, loads into pandas | **Tonight** | Backend |
| 2 | Enough experiments share fields (fuel, O₂, flow, g, result) to rank | Map 2 datasets to the schema | Fri 09:00–11:00 | Backend + Yusuf |
| 3 | LLM extraction from papers is accurate enough | Extract 10 fields from 2 papers, check by hand | Fri 11:00 | AI engineer |
| 4 | Judges accept a simplified model | Ask a mentor (06, Q3) | Fri morning | Hamza |
| 5 | The RAG answers stay grounded (no invented safety claims) | 10-question gold set, every answer cites | Fri 18:00 | AI engineer + Yusuf |
