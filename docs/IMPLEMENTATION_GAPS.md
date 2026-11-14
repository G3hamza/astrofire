# Implementation Gaps (honest list)

## Data that does not exist in the sources (left empty, not estimated)
- Material density, mass, surface area, composition, thermal properties: not in any NASA PSI table used.
- Measured cabin pressure for BASS, BASS-II, SAFFIRE, SAME, SAME-R, SPICE: assumed ~101.3 kPa.
- Oxygen and air flow for BASS (PSI-26): not in the table (only in BASS papers).
- Year for SAME-R and SPICE test dates.
- Outcomes for SAFFIRE-III and BASS: not recorded in the tables.
- Smoke detector readings for SAME/SAME-R: the tables hold test conditions only; detector time series are in the raw PSI files (not downloaded, GB-scale).
- PSI-62 (BASS modeling): no experimental table; reference only.
- Page numbers for RAG chunks: NTRS text extraction has no page markers (`page = null`).
- Scientific "finding vs interpretation" tagging of passages: not done; marked as such in `content_type`.

## Not built (proposed only)
- Iceberg / MinIO / Snowflake / vector DB / Prometheus / Grafana / cAdvisor (see TARGET_ARCHITECTURE.md).
- Docker image: files written, not run here (no Docker daemon).
- A validated predictive model: baseline fails to beat the majority class; not shipped.

## Needed to close the biggest scientific gap (Moon/Mars)
- Space or partial-gravity tests at 34% O2 / ~57 kPa for solid materials. None exist in public PSI data. The only partial-gravity numbers are 3 materials in one cited paper (`partial_gravity_limits.csv`).
