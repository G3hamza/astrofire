# Sources

## 1. Experiment data — NASA Physical Sciences Informatics (PSI), CC0
| Investigation | NASA page | DOI | Table rows |
|---|---|---|---|
| BASS-II (PSI-25) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-25 | 10.60555/4qc4-de67 | 129 |
| BASS (PSI-26) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-26 | 10.60555/58h4-dy80 | 122 |
| SAFFIRE-I (PSI-98) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-98 | 10.60555/0t15-1z43 | 4 |
| SAFFIRE-II (PSI-99) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-99 | 10.60555/2chp-m469 | 15 |
| SAFFIRE-III (PSI-100) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-100 | 10.60555/040q-4h36 | 2 |
| SAME (PSI-102) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-102 | 10.60555/gd4k-8h62 | 8 |
All 24 combustion investigations: links in data/processed/investigations.csv.

### Verified against NASA (12 Nov 2026)
Each experiment table above was downloaded from NASA PSI's official download endpoint
(`/geode-py/ws/studies/<ID>/download`) in the browser and compared with our file by SHA-256
(after removing the byte-order mark and normalising line endings). **All 6 tables are identical.**
| ID | SHA-256 (first 16) |
|---|---|
| PSI-25 | 19bc7964d79417cd |
| PSI-26 | 6cfe6dc04a944643 |
| PSI-98 | 723a31dd943a0062 |
| PSI-99 | 87c724671c9eb594 |
| PSI-100 | 851a1a5620d224bd |
| PSI-102 | 6eedcea74c20a715 |
The files were first collected through a public mirror of the official files
(https://github.com/Krypton-N/NASA-SPACE-APPS); the check above confirms they match NASA.

## 2. Papers — NASA Technical Reports Server (NTRS)
Not used by the app and not in this public repo (outside the challenge data scope). PSI investigation pages link to their own publications.

## 3. Standards
- NASA-STD-6001B with Change 3 (2025) — material flammability test standard (Test 1)
- JSC-29353B — flammability configuration analysis
- Test 1 paper — https://ntrs.nasa.gov/citations/20170004702

## 4. NASA Task Book — 138 combustion research projects. https://taskbook.nasaprs.com

## 5. Facts used in the pitch
- Materials can burn at lower O₂ in microgravity than in 1 g — Olson et al., ICES-2019: https://ttu-ir.tdl.org/items/1922ad9f-ef4c-4f52-96a4-980c23debe5e
- Exploration atmosphere 8.2 psia / 34% O₂ — https://ntrs.nasa.gov/citations/20220015741
- Test 1 data stored in MAPTIS — https://ntrs.nasa.gov/citations/20040084025
- BASS-II setup and sensors — https://ntrs.nasa.gov/citations/20150019858

## Assumptions (not NASA data)
- Pressure of space tests = 101.3 kPa (not listed in PSI tables).
- Moon and Mars habitat presets use the 8.2 psia / 34% O₂ exploration design point.
