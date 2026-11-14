# Data dictionary — data/processed/solids_tests.csv
| Column | Meaning |
|---|---|
| test_id | Investigation + NASA test number (e.g. BASS-II-O4) |
| accession / investigation / doi / psi_url | Where it came from in NASA PSI |
| platform | ISS Microgravity Science Glovebox, or uncrewed Cygnus (SAFFIRE) |
| gravity_g | 0 for all rows (space tests) |
| material_raw / material_family | NASA's text / our grouping (PMMA, cotton-fiberglass SIBAL, Nomex, silicone…) |
| geometry / thickness_mm | Parsed from the material text (film, rod, sphere, fabric) |
| o2_initial_pct / o2_final_pct | Calibrated O₂ % by volume (BASS-II), percent O₂ (SAFFIRE) |
| pressure_kpa / pressure_assumed | 101.3 kPa assumed (cabin), flagged True |
| flow_start_cm_s / flow_min_cm_s | Air display in cm/s; values > 40 are fan settings and are dropped |
| flow_direction | Concurrent / opposed (SAFFIRE) |
| outcome | burned · extinguished as flow was reduced · blowoff · did not ignite · extinguished when fan turned off · did not sustain · smoke test · not recorded |
| outcome_basis | stated (NASA note says it) / inferred (no event written) |
| ug_burn_length / one_g_burn_length | SAFFIRE-II: space vs Earth burn length for the same sample |
| notes_raw | NASA's original note, kept for traceability |

## Known limits
- BASS (PSI-26) table has materials only, no O₂/flow → used for counts, not for the map.
- 101 BASS-II outcomes are inferred (no extinction noted). Treat as "sustained at the listed flows".
- No PSI solid tests at partial gravity or low pressure. That is a real finding, shown as gaps.

## Added 13 Nov 2026
- 34 extra NASA NTRS papers (topic `exploration_gravity`): Saffire IV–VI results and models, lunar/Mars gravity flammability, exploration atmosphere 8.2 psia/34% O2. Fetched via NTRS API in Chrome. Corpus now 310 papers / 13,654 passages.
- `data/processed/partial_gravity_limits.csv`: 1 g vs Moon vs Mars vs 0 g oxygen limits for Mylar G, Ultem 1000, Nomex HT90-40 (Table I, NTRS 20130010991).
- `notebooks/astrofire_analysis.py`: 8-step Kaggle analysis.
