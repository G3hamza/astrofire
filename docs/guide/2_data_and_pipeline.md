# 2. The NASA data and the pipeline

## 2.1 Where the data comes from

**🧒 Simple version.** NASA keeps its space experiment results in an online library called **PSI** (Physical Sciences
Informatics). The challenge told us to use its **combustion** section. It has 24 experiments. We downloaded the *tables* of all
24 (small spreadsheets), not the huge videos.

**🛠️ Engineer version.**
- Source: https://psi.nasa.gov/physci/repo/search?q=combustion (the first link on the challenge resources tab). Licence: **CC0**.
- Local copy: `data/raw/psi/<PSI-ID>_<NAME>/` with `investigation.json` (metadata), `files_manifest.csv` (list of all files on PSI)
  and `Experimental table/*.csv` (the data we use).
- The huge PSI totals (BASS-II 255.8 GB, BASS 152.3 GB, SAFFIRE-III 32.8 GB) are videos, ISS photos and proof sheets of the same tests
  that are rows in the tables. They add no new conditions. See `docs/DATA_ACCESS.md`.
- **Not used (not on the challenge page):** NTRS papers. They are still in `data/raw/ntrs` and `data/curated` from earlier work, but
  the app does not read them.

## 2.2 All 24 investigations

| PSI ID | Name | What NASA did | Rows used | How AstroFire uses it |
|---|---|---|---|---|
| PSI-25 | **BASS-II** | Burned solid samples (PMMA, Nomex, cotton-fiberglass…) in a small wind tunnel on the ISS, lowering O₂ below 21% | 129 | **Core solid evidence** |
| PSI-26 | **BASS** | Earlier solid burns in the same glovebox | 121 | Solid evidence (many outcomes not recorded) |
| PSI-98/99/100 | **SAFFIRE I–III** | Large fires inside the uncrewed Cygnus cargo ship | 2 / 9 / 2 | Solid evidence |
| PSI-69 | **FLEX** | Burned fuel droplets at 12–34% O₂, 70–309 kPa, with N₂, CO₂ or He | 274 | Droplet flames ("atmosphere evidence") |
| PSI-39 | **CFI** | Cool-flame droplet tests at 0.5–5 atm, 17/21% O₂ | 79 unique | Droplet flames, outcome not recorded |
| PSI-68 | **FLEX-2** | Only a test matrix: condition ranges per fuel | 8 | Shown as matrix, never as tests |
| PSI-159 | **ACME CFI-G** | Gas-jet flames at 12–85% O₂, 0.5–3.3 bar, with NASA outcome codes | 333 | Gas flames ("atmosphere evidence") |
| PSI-10 | **ACME Flame Design** | Gas flames at 19.8–85% O₂, 43–306 kPa | 327 | Gas flames, outcome not recorded |
| PSI-20 | **ACME BRE** | Burner that imitates a burning solid; one row per test day | 18 days | Session log |
| PSI-21/22/23 | **ACME CLD / E-FIELD / s-Flame** | Gas flame test days | 32 / 32 / 18 | Session logs |
| PSI-106 | **SLICE** | Gas-jet flame test days | 12 | Session log |
| PSI-101/102 | **SAME-R / SAME** | Overheated (not burning) materials to measure smoke | 109 / 8 | Smoke tables per material |
| PSI-107 | **SPICE** | Gas-jet flames and soot (smoke point) | 469 (435 unique) | Soot context |
| PSI-142 | Cool-flame study | A list of 8 figures in a paper | 8 | Figure index |
| PSI-47 | **DAFT** | Dust sampling to check smoke counters | 2 | Sampling log |
| PSI-60/62/115/117 | Analysis / modeling projects | No data table on PSI | 0 | Listed for completeness |

## 2.3 The pipeline: Bronze → Silver → Gold

**🧒 Simple version.** Raw NASA spreadsheets are messy: different column names, units, typos, empty rows. The pipeline is a
program that cleans them step by step, like washing, sorting and labelling vegetables before cooking.
- **Bronze** = the original files, never touched.
- **Silver** = one clean table per experiment.
- **Gold** = the tables the app actually reads, organized by question.

Run it with one command: `python -m pipelines.orchestration.run_all`.

**🛠️ Engineer version.**

| Step | Code | What it does |
|---|---|---|
| Bronze manifest | `pipelines/ingestion/manifest.py` | Lists every raw file with SHA-256 hash and source URL → `data/manifests/bronze_manifest.csv`. A changed hash fails validation, so raw data is immutable |
| Silver | `pipelines/transformation/silver.py` | One function per investigation (`silver_bass2`, `silver_flex`, `silver_cfi`, `silver_acme_cfig`, …). Writes `data/silver/investigations/*.csv` |
| Gold | `pipelines/transformation/gold.py` | Builds analysis tables: `solid_fire_tests`, `droplet_extinction_tests`, `cool_flame_tests`, `gas_flame_tests`, `smoke_generation_tests`, `gas_jet_flame_conditions`, `mission_coverage`, KPIs → `data/gold/` |
| Validation | `pipelines/validation/validate.py` | 47 checks; the run fails if one fails |
| Docs | `pipelines/validation/dictionary.py` | Writes `docs/DATA_DICTIONARY.md`, `DATA_QUALITY_REPORT.md`, `PROVENANCE_REPORT.md` |
| Orchestration | `pipelines/orchestration/run_all.py` | Runs all of the above in order (~30 s) |

The investigation registry is `pipelines/common.py → INVESTIGATIONS` (folder, table file, role, kind, platform).

### Rules every Silver row follows
- **`record_id`** (e.g. `BASS-II-B1`, `FLEX-37`, `CFIG-N-21153F1`), **`source_file`** and **`source_row`**: you can always open
  the exact NASA row.
- **`source_record`**: the original row as JSON, kept untouched.
- **`*_status` columns** say how a value was obtained: `observed`, `inferred`, `assumed (ISS cabin; not in NASA table)`,
  `derived (atm x 101.325)`…
- **`quality_status`** = `valid` or `warning`, with the reason in `quality_notes`.
- Unusable rows go to **`data/quarantine/quarantine.csv`** with the rule that caught them. **Nothing is deleted.**

### Unit conversions
| From | To | Factor |
|---|---|---|
| mmHg (FLEX) | kPa | × 0.133322 |
| atm (CFI, ACME Flame Design) | kPa | × 101.325 |
| bar (ACME CFI-G) | kPa | × 100 |
| mole fraction (0.34) | % | × 100 |

### How outcomes are decided (the most important cleaning rule)
- **BASS-II** (`silver.py → bass2_outcome`): NASA wrote short notes per test. If the note says "ext", "out", "off" →
  *Extinction* (observed). "blowoff" → *Blowoff*. "no ign" → *No Ignition*. If the note only lists air flows and never says it went
  out → **Burned, but `inferred`**, because NASA didn't write "burned". Inferred outcomes are always badged and never used as
  reliable labels.
- **FLEX:** NASA's "test end" column: extinction / disruption / completion (completion = burned).
- **ACME CFI-G:** NASA's **SE / FT** column. *SE* → Extinction, *FT* → Burned until flow stopped; burn time 0 or "failed to ignite"
  in the comments → No Ignition. The "Hot ignition" column is **not used**: rows marked "No" still have burn times and comments like
  "hot flame", so it doesn't mean "no flame".
- **CFI, ACME Flame Design:** no outcome column → `not_recorded`. Never guessed.

### How materials are classified
- Only names NASA actually wrote count (`EXPLICIT` list: PMMA, SIBAL, Nomex, Ultem, silicone, wax…).
- Samples described only by shape ("black rod", "sphere") are **Unknown**. For BASS/BASS-II their *candidate* family is PMMA
  (low confidence, from the investigation context), shown as "family inferred".
- Fuels in droplet/gas experiments are classified as liquid or gaseous fuel, never as cabin materials.

### Pressure of space solid tests
The PSI tables for ISS/Cygnus solid tests **don't record pressure**. AstroFire assumes the cabin's **101.3 kPa** and labels it
**assumed** everywhere. FLEX, CFI and ACME pressures are measured (ACME CFI-G is "approx p").

## 2.4 Data problems we found in NASA's files (and what we did)

| Investigation | Problem | Fix |
|---|---|---|
| CFI | Rows 81–88 repeat rows 24–31 exactly | Copies quarantined (`duplicate:exact_row`); 79 unique tests |
| ACME CFI-G | 861 completely blank rows in the inverse-flame file | Skipped; logged as an info row in quarantine |
| ACME CFI-G | "Hot ignition = No" contradicts burn times | Column not used for outcomes |
| ACME BRE | "3400%" and "2100%" in the oxygen column | Read as 34% and 21%, warning logged |
| ACME s-Flame | "with N3", "with N4" | Read as N₂, note logged |
| FLEX | Header lost subscripts (O, N, CO) | Restored to O₂, N₂, CO₂ |
| SPICE | 34 exact duplicate rows | Kept in Silver, excluded from Gold |
| BASS | Rows without a test ID | Quarantined |

## 2.5 Gold tables the app reads

| Gold file | Rows | Content |
|---|---|---|
| `analytics/solid_fire_tests.csv` | 263 | Every solid-material space test with conditions, outcome, basis, source |
| `analytics/droplet_extinction_tests.csv` | 274 | FLEX |
| `analytics/cool_flame_tests.csv` | 79 | CFI |
| `analytics/gas_flame_tests.csv` | 660 | ACME CFI-G + Flame Design |
| `analytics/smoke_generation_tests.csv` | 117 | SAME + SAME-R |
| `analytics/gas_jet_flame_conditions.csv` | 435 | SPICE without duplicates |
| `analytics/mission_coverage.csv` | 4 | Solid tests near each mission atmosphere |
| `powerbi/kpis.csv`, `investigation_overview.csv`, `material_overview.csv`, `outcome_summary.csv`, `data_quality_overview.csv` | — | Numbers for Home, Experiments, Materials, Data quality |

Every Gold table also has a `.parquet` copy (pandas/pyarrow); CSV is the source of truth.

## 2.6 Key numbers (KPIs) and how they're computed

| KPI | Formula | Value |
|---|---|---|
| Solid fire tests in space | count of `solid_fire_tests` | 263 |
| Outcome written by NASA | observed / total × 100 | 14.8% |
| Outcome inferred | inferred / total × 100 | 38.4% |
| O₂ range of solid tests | min / max `o2_initial_pct` | 13.6–22.2% |
| Solid tests at Moon/Mars point | `mission_coverage` for Lunar + Mars | none (shown in words, not as 0) |
| Mission coverage rule | same gravity, O₂ within ±2 points, pressure within ±15 kPa | ISS: 62 |

## 2.7 Quality checks (47)

`validate.py → SPEC` defines, for each table: column types, required columns, allowed ranges (e.g. O₂ 0–100%, pressure 1–600 kPa).
Other checks: allowed vocabularies (`outcome_basis` ∈ observed / inferred / not_recorded / not_applicable), unique IDs, Bronze file
hashes, every Gold row traceable to an existing raw file, search/index files consistent. If any check fails the pipeline prints
**FAILED** and exits with code 1.
