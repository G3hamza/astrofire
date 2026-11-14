# Project Audit (Phase 1)

Audited 13 Nov 2026, before the data-layer rebuild. Raw data was not modified.

## What existed

| Area | Files | State |
|---|---|---|
| Raw NASA data | `data/raw/psi` (24 PSI combustion investigations, 16 with experiment tables), `data/raw/ntrs` (310 papers incl. 34 added 13 Nov), `data/raw/standards` (3 PDFs), `data/raw/taskbook` | Implemented. Mirrored from NASA PSI's public GitHub/S3 mirror, then 6 tables verified byte-for-byte (SHA-256) against psi.nasa.gov in Chrome. |
| ETL | `scripts/build_solids.py` (one merged table), `scripts/build_corpus.py` (chunks) | Partial: no layers, no manifest, no quarantine, no validation, no schemas. |
| Processed data | `data/processed/solids_tests.csv` (271 rows), `chunks.jsonl`, `papers.csv`, `investigations.csv`, `partial_gravity_limits.csv` | One generic table forced across BASS, BASS-II, SAFFIRE, SAME. |
| Backend | `backend/engine.py`, `backend/app.py` (FastAPI, 8 endpoints) | Working; read `data/processed`. |
| Tests / CI | none | Missing. |
| Docs | `README.md`, `docs/DATA.md`, `docs/SOURCES.md`, `docs/PLAN.html`, research plan | Product-level docs; no data model or contracts. |

## Six selected investigations: support before the rebuild

| Investigation | Raw table | Used by engine before | Issue |
|---|---|---|---|
| PSI-25 BASS-II | yes (129 tests) | yes | 101 outcomes inferred, not labelled as such in the material model |
| PSI-69 FLEX | yes (274 tests) | **no** | Not parsed at all; mixed UTF-8/Windows-1252 bytes; `–` used for missing |
| PSI-102 SAME | yes (8 rows) | yes, wrongly as a "fire test" | Smoke-generation test (heated, not burned) mixed into flame data |
| PSI-101 SAME-R | yes (109 rows) | **no** | Not parsed; dates have no year |
| PSI-98 SAFFIRE-I | yes (2 samples) | yes | 2 flow-visualization rows silently skipped |
| PSI-107 SPICE | yes (469 rows) | **no** | Not parsed; 34 exact duplicate rows; day-of-year without year |
| PSI-62 BASS modeling | no table (1 file, modeling) | n/a | Reference only, as specified |

## Scientific problems found

1. **Shape-based PMMA labelling:** 85 of 271 tests (31%) were labelled "PMMA" only because NASA's description said rod / sphere / film / micron. Fixed: these are now `material_family = Unknown`, with `candidate_family = PMMA` (investigation context, confidence none).
2. **Inferred outcomes treated like observed:** 101 BASS-II outcomes were derived from flow notes. Now `outcome_basis = inferred`, `label_reliable = False`, excluded from ML.
3. **Pressure never measured** for ISS/Cygnus solids: was a constant. Now `pressure_status = assumed`.
4. **Similarity share shown as probability** (`p_burn_nearby`). Renamed `nearby_burn_share` with explicit "NOT a calibrated probability" note; Moon/Mars/34% O2 inputs now return "Insufficient validated experimental evidence".
5. **Silent drops:** rows skipped without record. Now everything skipped goes to quarantine.
6. **Suspicious values:** e.g. BASS-II final O2 = 1.6% (initial 22.2%). Now set to missing, flagged, original kept.
