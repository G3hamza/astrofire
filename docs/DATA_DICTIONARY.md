# Data Dictionary

Auto-generated from the files by `pipelines/validation/dictionary.py`. Each file also has a `.parquet` copy and (Silver/Gold) a JSON Schema in `schemas/`.

## `data/silver/investigations/bass2_tests.csv` — 129 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 129/129 | BASS-II-B1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 129/129 | PSI-25 | NASA PSI accession (e.g. PSI-25). |
| investigation | 129/129 | BASS-II | Investigation acronym. |
| source_file | 129/129 | data/raw/psi/PSI-25_BASS-II/Experimental | Bronze file the row came from (path in repo). |
| source_row | 129/129 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 129/129 | {"PI": "Bhattacharjee", "Test #": "B1",  | Full original NASA row as JSON (nothing lost). |
| quality_notes | 60/129 | o2_final_pct=1.6 outside [10,40]; set to | Why the row was flagged. |
| pi | 129/129 | Bhattacharjee |  |
| test_number | 129/129 | B1 |  |
| test_date | 129/129 | 2014-02-19 |  |
| test_date_raw | 129/129 | 2/19/2014 |  |
| sample_number | 129/129 | 147 |  |
| material_id | 129/129 | MAT-pmma | FK -> silver/materials/materials.csv. |
| material_original_name | 129/129 | 100 micron PMMA film   2 cm wide | Material text exactly as NASA wrote it. |
| material_family | 129/129 | PMMA (acrylic) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| candidate_family | 57/129 | PMMA (acrylic) | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 129/129 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| geometry | 109/129 | thin film |  |
| thickness_mm | 35/129 | 0.1 | Sample thickness in mm, as labeled by NASA. |
| diameter_mm | 56/129 | 6.35 | Rod/sphere diameter in mm, converted from the NASA label (inches/cm). |
| gravity_g | 129/129 | 0.0 |  |
| gravity_status | 129/129 | observed (ISS) |  |
| o2_initial_pct | 129/129 | 22.2 | Initial O2, % by volume (observed). |
| o2_final_pct | 123/129 | 22.2 | Final O2, % by volume (observed). |
| co2_initial_pct | 127/129 | 0.44 |  |
| co2_final_pct | 123/129 | 0.44 |  |
| co_initial_ppm | 126/129 | 0.0 |  |
| co_final_ppm | 121/129 | 6.0 |  |
| pressure_kpa | 129/129 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 129/129 | assumed (ISS cabin; not in NASA table) | observed | assumed (...) |
| flow_start_cm_s | 122/129 | 5.0 | First air-flow setting, cm/s. |
| flow_min_cm_s | 122/129 | 5.0 | Lowest air-flow setting reached, cm/s. |
| flow_status | 129/129 | observed (air display) |  |
| air_display_raw | 125/129 | 5 |  |
| fan_display_raw | 116/129 | 62 |  |
| outcome_class | 129/129 | Burned | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 129/129 | inferred | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 129/129 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/bass_tests.csv` — 121 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 121/121 | BASS-1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 121/121 | PSI-26 | NASA PSI accession (e.g. PSI-25). |
| investigation | 121/121 | BASS | Investigation acronym. |
| source_file | 121/121 | data/raw/psi/PSI-26_BASS/Experimental ta | Bronze file the row came from (path in repo). |
| source_row | 121/121 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 121/121 | {"Date": "3/30/2012", "GMT": "90", "As R | Full original NASA row as JSON (nothing lost). |
| quality_notes | 30/121 | material not named in NASA table | Why the row was flagged. |
| test_date | 120/121 | 2012-03-30 |  |
| test_date_raw | 121/121 | 3/30/2012 |  |
| as_run_test_number | 121/121 | 1 |  |
| test_number | 121/121 | 1 |  |
| sample_number | 121/121 | 4 |  |
| material_id | 121/121 | MAT-sibal-cotton-fiberglass-fabric | FK -> silver/materials/materials.csv. |
| material_original_name | 121/121 | SIBAL 2 cm | Material text exactly as NASA wrote it. |
| material_family | 121/121 | Cotton-fiberglass (SIBAL) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| candidate_family | 30/121 | PMMA (acrylic) | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 121/121 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| geometry | 93/121 | fabric |  |
| diameter_mm | 47/121 | 20.0 | Rod/sphere diameter in mm, converted from the NASA label (inches/cm). |
| gravity_g | 121/121 | 0.0 |  |
| pressure_kpa | 121/121 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 121/121 | assumed (ISS cabin; not in NASA table) | observed | assumed (...) |
| o2_status | 121/121 | missing (not in NASA table; see BASS pap |  |
| flow_status | 121/121 | missing |  |
| outcome_class | 121/121 | Unknown | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 121/121 | not_recorded | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 121/121 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/saffire1_tests.csv` — 2 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 2/2 | SAFFIRE-I-S1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 2/2 | PSI-98 | NASA PSI accession (e.g. PSI-25). |
| investigation | 2/2 | SAFFIRE-I | Investigation acronym. |
| source_file | 2/2 | data/raw/psi/PSI-98_SAFFIRE-I/Experiment | Bronze file the row came from (path in repo). |
| source_row | 2/2 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 2/2 | {"Sample Number": "S1", "Material": "SIB | Full original NASA row as JSON (nothing lost). |
| quality_notes | 0/2 |  | Why the row was flagged. |
| sample_number | 2/2 | S1 |  |
| material_id | 2/2 | MAT-sibal-cotton-fiberglass-fabric | FK -> silver/materials/materials.csv. |
| material_original_name | 2/2 | SIBAL Fabric | Material text exactly as NASA wrote it. |
| material_family | 2/2 | Cotton-fiberglass (SIBAL) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| candidate_family | 0/2 |  | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 2/2 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| geometry | 2/2 | fabric |  |
| thickness_mm | 2/2 | 3.7 | Sample thickness in mm, as labeled by NASA. |
| length_cm | 2/2 | 40.6 |  |
| width_cm | 2/2 | 94.0 |  |
| gravity_g | 2/2 | 0.0 |  |
| o2_initial_pct | 2/2 | 21.5 | Initial O2, % by volume (observed). |
| o2_status | 2/2 | observed |  |
| o2_raw | 2/2 | 21.5 - 21.7 |  |
| pressure_kpa | 2/2 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 2/2 | assumed (Cygnus cabin ~ISS; not in NASA  | observed | assumed (...) |
| flow_cm_s | 2/2 | 20.0 | Air flow, cm/s. |
| flow_direction | 2/2 | Concurrent |  |
| ignition_power_w | 2/2 | 182.0 |  |
| ignition_time_s | 2/2 | 8.0 |  |
| burn_time_s | 2/2 | 420.0 |  |
| burn_time_raw | 2/2 | 420 |  |
| ug_burn_length_raw | 0/2 |  |  |
| one_g_burn_length_raw | 0/2 |  |  |
| one_g_spread_rate_raw | 0/2 |  |  |
| outcome_class | 2/2 | Burned | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 2/2 | observed | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 2/2 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/saffire2_tests.csv` — 9 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 9/9 | SAFFIRE-II-2-1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 9/9 | PSI-99 | NASA PSI accession (e.g. PSI-25). |
| investigation | 9/9 | SAFFIRE-II | Investigation acronym. |
| source_file | 9/9 | data/raw/psi/PSI-99_SAFFIRE-II/Experimen | Bronze file the row came from (path in repo). |
| source_row | 9/9 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 9/9 | {"Sample Number": "2-1", "Material": "Si | Full original NASA row as JSON (nothing lost). |
| quality_notes | 2/9 | material cell empty; carried from previo | Why the row was flagged. |
| sample_number | 9/9 | 2-1 |  |
| material_id | 9/9 | MAT-silicone | FK -> silver/materials/materials.csv. |
| material_original_name | 9/9 | Silicone | Material text exactly as NASA wrote it. |
| material_family | 9/9 | Silicone | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| candidate_family | 0/9 |  | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 9/9 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| geometry | 9/9 | sheet |  |
| thickness_mm | 9/9 | 0.27 | Sample thickness in mm, as labeled by NASA. |
| length_cm | 9/9 | 29.0 |  |
| width_cm | 9/9 | 5.0 |  |
| gravity_g | 9/9 | 0.0 |  |
| o2_initial_pct | 9/9 | 21.5 | Initial O2, % by volume (observed). |
| o2_status | 9/9 | observed |  |
| o2_raw | 9/9 | ~ 21.5 |  |
| pressure_kpa | 9/9 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 9/9 | assumed (Cygnus cabin ~ISS; not in NASA  | observed | assumed (...) |
| flow_cm_s | 9/9 | 20.0 | Air flow, cm/s. |
| flow_direction | 9/9 | Concurrent |  |
| ignition_power_w | 9/9 | 80.0 |  |
| ignition_time_s | 9/9 | 9.2 |  |
| burn_time_s | 5/9 | 145.0 |  |
| burn_time_raw | 9/9 | Insignificant |  |
| ug_burn_length_raw | 9/9 | ~ 0 |  |
| one_g_burn_length_raw | 9/9 | Complete |  |
| one_g_spread_rate_raw | 9/9 | Acceleratory |  |
| outcome_class | 9/9 | Not Sustained | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 9/9 | observed | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 9/9 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/saffire3_tests.csv` — 2 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 2/2 | SAFFIRE-III-S1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 2/2 | PSI-100 | NASA PSI accession (e.g. PSI-25). |
| investigation | 2/2 | SAFFIRE-III | Investigation acronym. |
| source_file | 2/2 | data/raw/psi/PSI-100_SAFFIRE-III/Experim | Bronze file the row came from (path in repo). |
| source_row | 2/2 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 2/2 | {"Sample Number": "S1", "Material": "SIB | Full original NASA row as JSON (nothing lost). |
| quality_notes | 0/2 |  | Why the row was flagged. |
| sample_number | 2/2 | S1 |  |
| material_id | 2/2 | MAT-sibal-cotton-fiberglass-fabric | FK -> silver/materials/materials.csv. |
| material_original_name | 2/2 | SIBAL Fabric | Material text exactly as NASA wrote it. |
| material_family | 2/2 | Cotton-fiberglass (SIBAL) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| candidate_family | 0/2 |  | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 2/2 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| geometry | 2/2 | fabric |  |
| thickness_mm | 2/2 | 3.3000000000000003 | Sample thickness in mm, as labeled by NASA. |
| length_cm | 2/2 | 94.0 |  |
| width_cm | 2/2 | 40.6 |  |
| gravity_g | 2/2 | 0.0 |  |
| o2_initial_pct | 0/2 |  | Initial O2, % by volume (observed). |
| o2_status | 2/2 | missing |  |
| o2_raw | 0/2 |  |  |
| pressure_kpa | 2/2 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 2/2 | assumed (Cygnus cabin ~ISS; not in NASA  | observed | assumed (...) |
| flow_cm_s | 2/2 | 30.0 | Air flow, cm/s. |
| flow_direction | 2/2 | Concurrent |  |
| ignition_power_w | 0/2 |  |  |
| ignition_time_s | 0/2 |  |  |
| burn_time_s | 0/2 |  |  |
| burn_time_raw | 0/2 |  |  |
| ug_burn_length_raw | 0/2 |  |  |
| one_g_burn_length_raw | 0/2 |  |  |
| one_g_spread_rate_raw | 0/2 |  |  |
| outcome_class | 2/2 | Unknown | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 2/2 | not_recorded | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 2/2 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/same_smoke_tests.csv` — 8 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 8/8 | SAME-1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 8/8 | PSI-102 | NASA PSI accession (e.g. PSI-25). |
| investigation | 8/8 | SAME | Investigation acronym. |
| source_file | 8/8 | data/raw/psi/PSI-102_SAME/Experimental t | Bronze file the row came from (path in repo). |
| source_row | 8/8 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 8/8 | {"Sample #": "1", "Sample Material": "Te | Full original NASA row as JSON (nothing lost). |
| quality_notes | 4/8 | NASA row says 'same conditions as 1-4';  | Why the row was flagged. |
| sample_number | 8/8 | 1 |  |
| material_id | 8/8 | MAT-teflon-ptfe | FK -> silver/materials/materials.csv. |
| material_original_name | 8/8 | Teflon | Material text exactly as NASA wrote it. |
| material_family | 8/8 | Fluoropolymer (PTFE) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| flow_cm_s | 4/8 | 5.0 | Air flow, cm/s. |
| weight_loss_rate_mg_min | 4/8 | 2.0 |  |
| aging_duration_min | 4/8 | 1.0 |  |
| gravity_g | 8/8 | 0.0 |  |
| pressure_kpa | 8/8 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 8/8 | assumed (ISS cabin) | observed | assumed (...) |
| test_type | 8/8 | smoke generation (heated, not burned) |  |
| outcome_class | 8/8 | Not a flame test | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 8/8 | not_applicable | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 8/8 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/same_r_smoke_tests.csv` — 109 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 109/109 | SAME-R-kapton-51 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 109/109 | PSI-101 | NASA PSI accession (e.g. PSI-25). |
| investigation | 109/109 | SAME-R | Investigation acronym. |
| source_file | 109/109 | data/raw/psi/PSI-101_SAME-R/Experimental | Bronze file the row came from (path in repo). |
| source_row | 109/109 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 109/109 | {"Sample Type": "Kapton", "SAME Test #": | Full original NASA row as JSON (nothing lost). |
| quality_notes | 0/109 |  | Why the row was flagged. |
| material_id | 109/109 | MAT-kapton | FK -> silver/materials/materials.csv. |
| material_original_name | 109/109 | Kapton | Material text exactly as NASA wrote it. |
| material_family | 109/109 | Polyimide (Kapton) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| same_test_number | 109/109 | 51 |  |
| parent_test_number | 42/109 | 51 |  |
| is_aged_measurement | 109/109 | False |  |
| description | 109/109 | B.L. new formula |  |
| date_raw | 109/109 | 21-Jul |  |
| date_status | 109/109 | partial (day-month only; year not in NAS |  |
| inlet_velocity_cm_s | 109/109 | 8.1 |  |
| heater_resistance_ratio | 109/109 | 1.38 |  |
| duration_s | 68/109 | 60.0 |  |
| primary_aging_time_s | 67/109 | 11.0 |  |
| primary_mixing_time_s | 67/109 | 8.0 |  |
| net_aging_time_s | 104/109 | 38.0 |  |
| gravity_g | 109/109 | 0.0 |  |
| pressure_kpa | 109/109 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 109/109 | assumed (ISS cabin) | observed | assumed (...) |
| test_type | 109/109 | smoke generation (heated, not burned) |  |
| outcome_class | 109/109 | Not a flame test | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 109/109 | not_applicable | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 109/109 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/flex_droplet_tests.csv` — 274 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 274/274 | FLEX-1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 274/274 | PSI-69 | NASA PSI accession (e.g. PSI-25). |
| investigation | 274/274 | FLEX | Investigation acronym. |
| source_file | 274/274 | data/raw/psi/PSI-69_FLEX/Experimental ta | Bronze file the row came from (path in repo). |
| source_row | 274/274 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 274/274 | {"FLEX Test #": "1", "FLEX Identifier":  | Full original NASA row as JSON (nothing lost). |
| quality_notes | 37/274 | NASA marked some values with '–' (treate | Why the row was flagged. |
| flex_test_number | 274/274 | 1 |  |
| flex_identifier | 274/274 | 20CAL08 |  |
| test_date | 274/274 | 2009-03-05 |  |
| test_date_raw | 274/274 | 3/5/2009 |  |
| test_gmt | 273/274 | 17:22:03 |  |
| fuel | 274/274 | Methanol |  |
| material_id | 274/274 | MAT-methanol | FK -> silver/materials/materials.csv. |
| material_family | 274/274 | Liquid fuel (droplet) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| pressure_mmhg | 274/274 | 757.7 |  |
| pressure_kpa | 273/274 | 101.02 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 274/274 | observed | observed | assumed (...) |
| o2_pct | 274/274 | 21.0 | O2 mole fraction x 100 (FLEX). |
| n2_pct | 274/274 | 79.0 | N2 mole fraction x 100. |
| co2_pct | 274/274 | 0.0 | CO2 mole fraction x 100 (FLEX header 'CO' restored to CO2). |
| he_pct | 274/274 | 0.0 | Helium mole fraction x 100. |
| diluent_note | 274/274 | header subscripts restored (O->O2, N->N2 |  |
| droplet_initial_diameter_mm | 262/274 | 1.69 |  |
| extinction_diameter_mm | 197/274 | 0.89 |  |
| burning_rate_as_labeled | 258/274 | 0.52 | FLEX 'Burning rate; mm' value, unit kept as NASA labeled it. |
| burning_rate_unit_as_labeled | 274/274 | mm (as labeled by NASA; burning-rate con |  |
| burn_time_s | 268/274 | 4.3 |  |
| test_end_raw | 274/274 | Disruption |  |
| gravity_g | 274/274 | 0.0 |  |
| outcome_class | 274/274 | Disruption | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 274/274 | observed | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 274/274 | valid | valid | warning (see quality_notes). |

## `data/silver/investigations/spice_flames.csv` — 469 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 469/469 | SPICE-r0001 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 469/469 | PSI-107 | NASA PSI accession (e.g. PSI-25). |
| investigation | 469/469 | SPICE | Investigation acronym. |
| source_file | 469/469 | data/raw/psi/PSI-107_SPICE/Experimental  | Bronze file the row came from (path in repo). |
| source_row | 469/469 | 2 | Line number in the NASA CSV (header = line 1). |
| source_record | 469/469 | {"GMT date": "45", "GMT ignition": "14:3 | Full original NASA row as JSON (nothing lost). |
| quality_notes | 34/469 | exact duplicate of SPICE-r0001 (kept; ex | Why the row was flagged. |
| gmt_day_of_year | 469/469 | 45.0 |  |
| date_status | 469/469 | partial (day-of-year only; year not in N |  |
| gmt_ignition | 469/469 | 14:37:08 |  |
| gmt_flame_off | 458/469 | 14:48:03 |  |
| fuel | 469/469 | Ethylene |  |
| material_id | 469/469 | MAT-ethylene | FK -> silver/materials/materials.csv. |
| material_family | 469/469 | Gaseous fuel | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| nozzle_diameter_mm | 469/469 | 1.6002 |  |
| fuel_rate_sccm | 457/469 | 103.8 |  |
| fuel_rate_mg_s | 457/469 | 1.971 |  |
| hc_fuel_rate_mg_s | 469/469 | 1.971 |  |
| air_velocity_cm_s | 444/469 | 36.39 |  |
| gravity_g | 469/469 | 0.0 |  |
| pressure_kpa | 469/469 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 469/469 | assumed (ISS cabin) | observed | assumed (...) |
| duplicate_of | 34/469 | SPICE-r0001 | SPICE: record this row exactly duplicates (excluded from Gold). |
| quality_status | 469/469 | valid | valid | warning (see quality_notes). |

## `data/silver/materials/materials.csv` — 36 rows

| column | filled | example | meaning |
|---|---|---|---|
| material_id | 36/36 | MAT-30-butane | FK -> silver/materials/materials.csv. |
| material_normalized_name | 36/36 | 30% butane |  |
| material_family | 36/36 | Gaseous fuel | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| candidate_family | 5/36 | PMMA (acrylic) | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 36/36 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| classification_confidence | 36/36 | high | high | none. |
| physical_form | 36/36 | gas |  |
| chemical_name | 0/36 |  |  |
| material_composition | 0/36 |  |  |
| manufacturer | 0/36 |  |  |
| material_description | 0/36 |  |  |
| original_names | 36/36 | 30% butane |  |
| investigations | 36/36 | ACME CFI-G |  |
| source_reference | 36/36 | https://psi.nasa.gov/physci/repo/data/in |  |

## `data/silver/materials/material_samples.csv` — 1862 rows

| column | filled | example | meaning |
|---|---|---|---|
| sample_id | 1862/1862 | BASS-II-B1-S |  |
| record_id | 1862/1862 | BASS-II-B1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 1862/1862 | PSI-25 | NASA PSI accession (e.g. PSI-25). |
| material_id | 1862/1862 | MAT-pmma | FK -> silver/materials/materials.csv. |
| material_original_name | 1862/1862 | 100 micron PMMA film   2 cm wide | Material text exactly as NASA wrote it. |
| material_family | 1862/1862 | PMMA (acrylic) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| candidate_family | 87/1862 | PMMA (acrylic) | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 1862/1862 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| geometry | 208/1862 | thin film |  |
| source_file | 1862/1862 | data/raw/psi/PSI-25_BASS-II/Experimental | Bronze file the row came from (path in repo). |
| source_row | 1862/1862 | 2 | Line number in the NASA CSV (header = line 1). |

## `data/silver/materials/material_properties.csv` — 258 rows

| column | filled | example | meaning |
|---|---|---|---|
| property_id | 258/258 | BASS-II-B1-S-thickness |  |
| sample_id | 258/258 | BASS-II-B1-S |  |
| material_id | 258/258 | MAT-pmma | FK -> silver/materials/materials.csv. |
| property | 258/258 | thickness |  |
| value | 258/258 | 0.1 |  |
| unit | 205/258 | mm | Unit of value. |
| value_status | 258/258 | observed (as labeled in NASA table) | observed | derived (formula) | assumed. |
| source_file | 258/258 | data/raw/psi/PSI-25_BASS-II/Experimental | Bronze file the row came from (path in repo). |
| source_row | 258/258 | 2 | Line number in the NASA CSV (header = line 1). |

## `data/silver/measurements/measurements.csv` — 6589 rows

| column | filled | example | meaning |
|---|---|---|---|
| measurement_id | 6589/6589 | BASS-II-B1/o2_initial_pct |  |
| record_id | 6589/6589 | BASS-II-B1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation_id | 6589/6589 | PSI-25 | NASA PSI accession (e.g. PSI-25). |
| quantity | 6589/6589 | o2_initial_pct | Measured quantity name. |
| value | 6589/6589 | 22.2 |  |
| unit | 6589/6589 | %vol | Unit of value. |
| value_status | 6589/6589 | observed | observed | derived (formula) | assumed. |
| source_column | 6589/6589 | Calibrated  initial O2 % by vol |  |
| source_file | 6589/6589 | data/raw/psi/PSI-25_BASS-II/Experimental | Bronze file the row came from (path in repo). |
| source_row | 6589/6589 | 2 | Line number in the NASA CSV (header = line 1). |

## `data/gold/analytics/solid_fire_tests.csv` — 263 rows

| column | filled | example | meaning |
|---|---|---|---|
| test_id | 263/263 | BASS-II-B1 | Same as Silver record_id. |
| investigation_id | 263/263 | PSI-25 | NASA PSI accession (e.g. PSI-25). |
| investigation | 263/263 | BASS-II | Investigation acronym. |
| platform | 263/263 | ISS MSG |  |
| gravity_g | 263/263 | 0.0 |  |
| material_id | 263/263 | MAT-pmma | FK -> silver/materials/materials.csv. |
| material_raw | 263/263 | 100 micron PMMA film   2 cm wide |  |
| material_family | 263/263 | PMMA (acrylic) | Family from an explicit name only; 'Unknown' if NASA did not name it. |
| material_family_effective | 263/263 | PMMA (acrylic) | material_family, or candidate_family when unknown. Use together with material_identity. |
| material_identity | 263/263 | named in NASA table | named in NASA table | not named; family inferred from investigation context | unknown. |
| geometry | 215/263 | thin film |  |
| thickness_mm | 48/263 | 0.1 | Sample thickness in mm, as labeled by NASA. |
| diameter_mm | 103/263 | 6.35 | Rod/sphere diameter in mm, converted from the NASA label (inches/cm). |
| o2_initial_pct | 140/263 | 22.2 | Initial O2, % by volume (observed). |
| o2_final_pct | 123/263 | 22.2 | Final O2, % by volume (observed). |
| pressure_kpa | 263/263 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| pressure_status | 263/263 | assumed (ISS cabin; not in NASA table) | observed | assumed (...) |
| flow_start_cm_s | 135/263 | 5.0 | First air-flow setting, cm/s. |
| flow_min_cm_s | 135/263 | 5.0 | Lowest air-flow setting reached, cm/s. |
| flow_direction | 13/263 | Concurrent |  |
| outcome_class | 263/263 | Burned | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 263/263 | inferred | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| label_reliable | 263/263 | False | True only when outcome_basis = observed. |
| burn_time_s | 7/263 | 420.0 |  |
| ug_burn_length | 9/263 | ~ 0 |  |
| one_g_burn_length | 9/263 | Complete |  |
| test_date | 249/263 | 2014-02-19 |  |
| quality_status | 263/263 | valid | valid | warning (see quality_notes). |
| quality_notes | 92/263 | o2_final_pct=1.6 outside [10,40]; set to | Why the row was flagged. |
| notes_raw | 263/263 | air display: 5 / fan: 62 |  |
| source_file | 263/263 | data/raw/psi/PSI-25_BASS-II/Experimental | Bronze file the row came from (path in repo). |
| source_row | 263/263 | 2 | Line number in the NASA CSV (header = line 1). |
| psi_url | 263/263 | https://psi.nasa.gov/physci/repo/data/in |  |
| doi | 263/263 | 10.60555/4qc4-de67 |  |

## `data/gold/analytics/droplet_extinction_tests.csv` — 274 rows

| column | filled | example | meaning |
|---|---|---|---|
| test_id | 274/274 | FLEX-1 | Same as Silver record_id. |
| fuel | 274/274 | Methanol |  |
| material_id | 274/274 | MAT-methanol | FK -> silver/materials/materials.csv. |
| test_date | 274/274 | 2009-03-05 |  |
| pressure_kpa | 273/274 | 101.02 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| o2_pct | 274/274 | 21.0 | O2 mole fraction x 100 (FLEX). |
| n2_pct | 274/274 | 79.0 | N2 mole fraction x 100. |
| co2_pct | 274/274 | 0.0 | CO2 mole fraction x 100 (FLEX header 'CO' restored to CO2). |
| he_pct | 274/274 | 0.0 | Helium mole fraction x 100. |
| diluent | 274/274 | N2 (air-like) |  |
| droplet_initial_diameter_mm | 262/274 | 1.69 |  |
| extinction_diameter_mm | 197/274 | 0.89 |  |
| burn_time_s | 268/274 | 4.3 |  |
| outcome_class | 274/274 | Disruption | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 274/274 | observed | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| quality_status | 274/274 | valid | valid | warning (see quality_notes). |
| source_file | 274/274 | data/raw/psi/PSI-69_FLEX/Experimental ta | Bronze file the row came from (path in repo). |
| source_row | 274/274 | 2 | Line number in the NASA CSV (header = line 1). |
| psi_url | 274/274 | https://psi.nasa.gov/physci/repo/data/in |  |

## `data/gold/analytics/gas_jet_flame_conditions.csv` — 435 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 435/435 | SPICE-r0001 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| fuel | 435/435 | Ethylene |  |
| material_id | 435/435 | MAT-ethylene | FK -> silver/materials/materials.csv. |
| nozzle_diameter_mm | 435/435 | 1.6002 |  |
| fuel_rate_mg_s | 428/435 | 1.971 |  |
| air_velocity_cm_s | 415/435 | 36.39 |  |
| gmt_day_of_year | 435/435 | 45.0 |  |
| source_file | 435/435 | data/raw/psi/PSI-107_SPICE/Experimental  | Bronze file the row came from (path in repo). |
| source_row | 435/435 | 2 | Line number in the NASA CSV (header = line 1). |
| psi_url | 435/435 | https://psi.nasa.gov/physci/repo/data/in |  |

## `data/gold/analytics/smoke_generation_tests.csv` — 117 rows

| column | filled | example | meaning |
|---|---|---|---|
| record_id | 117/117 | SAME-1 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| investigation | 117/117 | SAME | Investigation acronym. |
| material_id | 117/117 | MAT-teflon-ptfe | FK -> silver/materials/materials.csv. |
| material | 117/117 | Teflon |  |
| flow_cm_s | 113/117 | 5.0 | Air flow, cm/s. |
| heater_resistance_ratio | 109/117 | 1.38 |  |
| aging_time_s | 108/117 | 60.0 |  |
| is_aged_measurement | 109/117 | False |  |
| weight_loss_rate_mg_min | 4/117 | 2.0 |  |
| source_file | 117/117 | data/raw/psi/PSI-102_SAME/Experimental t | Bronze file the row came from (path in repo). |
| source_row | 117/117 | 2 | Line number in the NASA CSV (header = line 1). |

## `data/gold/analytics/mission_coverage.csv` — 4 rows

| column | filled | example | meaning |
|---|---|---|---|
| mission | 4/4 | ISS cabin |  |
| gravity_g | 4/4 | 0.0 |  |
| o2_pct | 4/4 | 21.0 | O2 mole fraction x 100 (FLEX). |
| pressure_kpa | 4/4 | 101.3 | Ambient pressure, kPa. ISS/Cygnus solids: ASSUMED 101.3 (see pressure_status). FLEX: measured. |
| space_solid_tests_near | 4/4 | 62 |  |
| space_tests_near_observed_outcome | 4/4 | 18 |  |
| rule | 4/4 | same gravity, O2 within 2 points, pressu |  |

## `data/gold/analytics/investigation_profiles.csv` — 24 rows

| column | filled | example | meaning |
|---|---|---|---|
| investigation_id | 24/24 | PSI-26 | NASA PSI accession (e.g. PSI-25). |
| acronym | 24/24 | BASS |  |
| title | 24/24 | Burning and Suppression of Solids |  |
| pillar | 24/24 | prevention |  |
| pillar_secondary | 10/24 | suppression |  |
| relevance_tier | 24/24 | direct |  |
| hardware_family | 24/24 | MSG flow duct |  |
| fuel_phase | 24/24 | solid |  |
| study_type | 24/24 | flight |  |
| records | 24/24 | 121 |  |
| o2_min_pct | 8/24 | 13.6 |  |
| o2_max_pct | 8/24 | 22.2 |  |
| varied_factors | 18/24 | Material (NASA name); Material family; S |  |
| sensors | 21/24 | Video / cameras |  |
| publications | 24/24 | 10 |  |
| data_files | 24/24 | 212 |  |
| psi_url | 24/24 | https://psi.nasa.gov/physci/repo/data/in |  |

## `data/gold/powerbi/investigation_overview.csv` — 24 rows

| column | filled | example | meaning |
|---|---|---|---|
| investigation_id | 24/24 | PSI-25 | NASA PSI accession (e.g. PSI-25). |
| acronym | 24/24 | BASS-II |  |
| role | 24/24 | primary |  |
| experiment_kind | 24/24 | solid_flame_spread |  |
| platform | 24/24 | ISS MSG |  |
| title | 24/24 | Burning and Suppression of Solids - II |  |
| doi | 24/24 | 10.60555/4qc4-de67 |  |
| start_date | 21/24 | 01-01-2010 |  |
| end_date | 20/24 | 12-31-2022 |  |
| records | 24/24 | 129 |  |
| records_with_warnings | 24/24 | 60 |  |
| has_experimental_table | 24/24 | True |  |
| psi_url | 24/24 | https://psi.nasa.gov/physci/repo/data/in |  |

## `data/gold/powerbi/material_overview.csv` — 36 rows

| column | filled | example | meaning |
|---|---|---|---|
| material_id | 36/36 | MAT-30-butane | FK -> silver/materials/materials.csv. |
| material | 36/36 | 30% butane |  |
| family | 36/36 | Gaseous fuel |  |
| candidate_family | 5/36 | PMMA (acrylic) | Low-confidence family from investigation context (e.g. BASS-II rods). Never used as the classified family. |
| classification_basis | 36/36 | explicit_name | explicit_name | unknown_shape_only | unknown. |
| investigations | 36/36 | ACME CFI-G |  |
| samples | 36/36 | 52 |  |
| solid_flame_tests | 36/36 | 0 |  |
| observed_outcomes | 36/36 | 0 |  |
| burned | 36/36 | 0 |  |
| went_out | 36/36 | 0 |  |
| properties_available | 9/36 | color, diameter, length, thickness, widt |  |
| properties_missing | 36/36 | density, mass, thermal properties, compo |  |

## `data/gold/powerbi/outcome_summary.csv` — 9 rows

| column | filled | example | meaning |
|---|---|---|---|
| investigation | 9/9 | BASS | Investigation acronym. |
| outcome_class | 9/9 | Unknown | Burned | Extinction | Blowoff | No Ignition | Not Sustained | Disruption | Not a flame test | Unknown. |
| outcome_basis | 9/9 | not_recorded | observed (NASA wrote it) | inferred (derived from notes) | not_recorded | not_applicable. |
| tests | 9/9 | 121 |  |

## `data/gold/powerbi/data_quality_overview.csv` — 15 rows

| column | filled | example | meaning |
|---|---|---|---|
| table | 15/15 | bass2_tests |  |
| records | 15/15 | 129 |  |
| valid | 15/15 | 69 |  |
| warnings | 15/15 | 60 |  |
| pct_valid | 15/15 | 53.5 |  |

## `data/gold/powerbi/kpis.csv` — 13 rows

| column | filled | example | meaning |
|---|---|---|---|
| kpi | 13/13 | solid_flame_tests_total |  |
| formula | 13/13 | count(gold/analytics/solid_fire_tests) |  |
| value | 13/13 | 263 |  |
| unit | 13/13 | tests | Unit of value. |
| refreshed_at | 13/13 | 2026-11-14T00:38:38Z |  |

## `data/gold/ml/solid_outcome_features.csv` — 33 rows

| column | filled | example | meaning |
|---|---|---|---|
| test_id | 33/33 | BASS-II-B14 | Same as Silver record_id. |
| o2_initial_pct | 33/33 | 15.0 | Initial O2, % by volume (observed). |
| flow_min_cm_s | 33/33 | 2.0 | Lowest air-flow setting reached, cm/s. |
| thickness_mm | 16/33 | 0.2 | Sample thickness in mm, as labeled by NASA. |
| diameter_mm | 17/33 | 9.52 | Rod/sphere diameter in mm, converted from the NASA label (inches/cm). |
| geometry | 32/33 | thin film |  |
| material_family_effective | 33/33 | PMMA (acrylic) | material_family, or candidate_family when unknown. Use together with material_identity. |
| material_identity | 33/33 | named in NASA table | named in NASA table | not named; family inferred from investigation context | unknown. |
| target_burned | 33/33 | 0 |  |
| label_source | 33/33 | observed (NASA note) |  |
| split | 33/33 | test | train | test (grouped by investigation+date). |
| split_group | 33/33 | BASS-II/2014-07-02 |  |
| source_file | 33/33 | data/raw/psi/PSI-25_BASS-II/Experimental | Bronze file the row came from (path in repo). |
| source_row | 33/33 | 15 | Line number in the NASA CSV (header = line 1). |

## `data/quarantine/quarantine.csv` — 71 rows

| column | filled | example | meaning |
|---|---|---|---|
| original_record | 71/71 | "{\"PI\": \"Bhattacharjee\", \"Test #\": |  |
| source_file | 71/71 | data/raw/psi/PSI-25_BASS-II/Experimental | Bronze file the row came from (path in repo). |
| investigation | 71/71 | BASS-II | Investigation acronym. |
| record_id | 69/71 | BASS-II-B2 | Unique record id within AstroFire (investigation acronym + NASA test/sample number). |
| failure_reason | 71/71 | o2_final_pct=1.6 outside plausible range |  |
| validation_rule | 71/71 | range:o2_pct |  |
| severity | 71/71 | warn |  |
| processed_at | 71/71 | 2026-11-14T00:38:38Z |  |
