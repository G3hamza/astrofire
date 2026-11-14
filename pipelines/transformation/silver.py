"""Silver layer: one cleaned, investigation-specific table per NASA investigation.

Each Silver record keeps:
  record_id, investigation_id, source_file, source_row (line number in the NASA CSV, header = 1),
  source_record (the full original row as JSON), normalized columns, *_status columns
  (observed / inferred / assumed / missing), quality_status, quality_notes.

Also builds the shared scientific entities:
  silver/materials/materials.csv            one row per distinct material (normalized)
  silver/materials/material_samples.csv     one row per tested specimen (links record -> material)
  silver/materials/material_properties.csv  long table: property, value, unit, status, source
  silver/measurements/measurements.csv      long table of every numeric measurement, with unit + provenance
Rejected / suspicious rows go to data/quarantine/quarantine.csv (never silently dropped).
"""
import json, re
from collections import Counter, defaultdict
from datetime import datetime
from pipelines.common import (PSI, INVESTIGATIONS, SILVER, QUAR, ISS_KPA, MMHG_TO_KPA, Quarantine, table_path, rel,
                              read_csv_rows, write_csv, nums, first_num, slug, psi_url)

Q = Quarantine()
MEAS, SAMPLES, PROPS = [], [], []
MATERIALS = {}

# ---------------------------------------------------------------- material classification
EXPLICIT = [  # (pattern, normalized name, family). Only names that NASA actually wrote.
    (r"pmma", "PMMA", "PMMA (acrylic)"),
    (r"sibal|cotton[- ]?fiberglass", "SIBAL cotton-fiberglass fabric", "Cotton-fiberglass (SIBAL)"),
    (r"nomex", "Nomex", "Aramid fabric (Nomex)"),
    (r"silicone", "Silicone", "Silicone"),
    (r"ultem", "Ultem", "Polyetherimide (Ultem)"),
    (r"teflon|ptfe", "Teflon (PTFE)", "Fluoropolymer (PTFE)"),
    (r"kapton", "Kapton", "Polyimide (Kapton)"),
    (r"pyrell", "Pyrell foam", "Foam (Pyrell)"),
    (r"lampwick", "Lampwick", "Cotton (lampwick)"),
    (r"dibutyl", "Dibutyl phthalate", "Plasticizer liquid (DBP)"),
    (r"wax|candle", "Wax", "Wax"),
]
SHAPE_ONLY = r"\b(rod|sphere|spherical|film|slab|micron)\b"
# Investigations whose own papers describe their unnamed rods/spheres/films as PMMA. Used ONLY as a
# low-confidence candidate family, never as the classified family.
CONTEXT_CANDIDATE = {"PSI-25": "PMMA (acrylic)", "PSI-26": "PMMA (acrylic)"}


def classify(text, acc, kind="solid"):
    """Return dict(material_normalized_name, material_family, classification_basis, classification_confidence, candidate_family)."""
    t = (text or "").lower()
    if kind == "liquid_fuel":
        return dict(material_normalized_name=text.strip().title(), material_family="Liquid fuel (droplet)",
                    classification_basis="explicit_name", classification_confidence="high", candidate_family="")
    if kind == "gas_fuel":
        n = re.sub(r"\s*%\s*", "% ", text.strip())
        return dict(material_normalized_name=n, material_family="Gaseous fuel",
                    classification_basis="explicit_name", classification_confidence="high", candidate_family="")
    hits = [(n, f) for p, n, f in EXPLICIT if re.search(p, t)]
    if len({f for _, f in hits}) > 1:
        return dict(material_normalized_name=" + ".join(n for n, _ in hits), material_family="Mixed sample",
                    classification_basis="explicit_name", classification_confidence="high", candidate_family="")
    if hits:
        return dict(material_normalized_name=hits[0][0], material_family=hits[0][1],
                    classification_basis="explicit_name", classification_confidence="high", candidate_family="")
    if re.search(SHAPE_ONLY, t):
        shape = re.search(SHAPE_ONLY, t).group(1).replace("spherical", "sphere").replace("micron", "film")
        color = next((c for c in ("clear", "black") if c in t), "")
        return dict(material_normalized_name=f"Unnamed {color + ' ' if color else ''}{shape}".strip(), material_family="Unknown",
                    classification_basis="unknown_shape_only", classification_confidence="none",
                    candidate_family=CONTEXT_CANDIDATE.get(acc, ""))
    return dict(material_normalized_name=text.strip() or "Unrecorded", material_family="Unknown",
                classification_basis="unknown", classification_confidence="none", candidate_family="")


def register_material(original, acc, kind="solid"):
    c = classify(original, acc, kind)
    mid = "MAT-" + slug(c["material_normalized_name"])
    m = MATERIALS.setdefault(mid, dict(material_id=mid, **c, physical_form=dict(solid="solid", liquid_fuel="liquid", gas_fuel="gas").get(kind, ""),
                                       original_names=set(), investigations=set(), chemical_name="", material_composition="",
                                       manufacturer="", source_reference=set()))
    m["original_names"].add(original.strip()); m["investigations"].add(INVESTIGATIONS[acc]["acronym"]); m["source_reference"].add(psi_url(acc))
    return mid, c


# ---------------------------------------------------------------- specimen geometry (as labeled)
def inch(s):
    if (x := re.search(r'(\d+)\s*/\s*(\d+)\s*"?', s)): return float(x.group(1)) / float(x.group(2)) * 25.4
    if (x := re.search(r'(\d*\.?\d+)\s*"', s)): return float(x.group(1)) * 25.4
    return None


def specimen(text):
    """Pull dimensions that NASA wrote in the material cell. Returns {property: (value, unit)}."""
    t = (text or "").lower(); out = {}
    if (x := re.match(r"\s*0(\d+)\s*mm", t)): out["thickness"] = (float("0." + x.group(1)), "mm")  # SAFFIRE-II writes 0.37 mm as "037 mm"
    elif (x := re.search(r"(\d+(?:\.\d+)?)\s*micron", t)): out["thickness"] = (float(x.group(1)) / 1000, "mm")
    elif (x := re.search(r"(\d+(?:\.\d+)?)\s*mm\s*thick", t)): out["thickness"] = (float(x.group(1)), "mm")
    if "rod" in t and (d := inch(t)) is not None: out["diameter"] = (round(d, 2), "mm")
    if "rod" in t and re.search(r"\b1/4\b", t) and "diameter" not in out: out["diameter"] = (6.35, "mm")
    if re.search(r"sphere|spherical", t) and (x := re.search(r"(\d+(?:\.\d+)?)\s*cm", t)): out["diameter"] = (float(x.group(1)) * 10, "mm")
    if (x := re.search(r"(\d+(?:\.\d+)?)\s*cm\s*wide", t)): out["width"] = (float(x.group(1)) * 10, "mm")
    for c in ("clear", "black"):
        if c in t: out["color"] = (c, "")
    geo = next((g for k, g in [("sphere", "sphere"), ("spherical", "spherical section"), ("rod", "rod"), ("film", "thin film"),
                                ("micron", "thin film"), ("slab", "slab"), ("fabric", "fabric"), ("sibal", "fabric"), ("candle", "candle")] if k in t), "")
    return out, geo


def add_sample(record_id, acc, original, src_file, src_row, extra=None, kind="solid"):
    mid, c = register_material(original, acc, kind)
    dims, geo = specimen(original) if kind == "solid" else ({}, "")
    for k, v in (extra or {}).items():
        if v[0] is not None and k not in dims: dims[k] = v
    sid = f"{record_id}-S"
    SAMPLES.append(dict(sample_id=sid, record_id=record_id, investigation_id=acc, material_id=mid,
                        material_original_name=original, material_family=c["material_family"],
                        candidate_family=c["candidate_family"], classification_basis=c["classification_basis"],
                        geometry=geo, source_file=src_file, source_row=src_row))
    for p, (v, u) in dims.items():
        PROPS.append(dict(property_id=f"{sid}-{p}", sample_id=sid, material_id=mid, property=p, value=v, unit=u,
                          value_status="observed (as labeled in NASA table)", source_file=src_file, source_row=src_row))
    return mid, c, dims, geo


def meas(record_id, acc, quantity, value, unit, status, col, src_file, src_row):
    if value is None or value == "": return
    MEAS.append(dict(measurement_id=f"{record_id}|{quantity}", record_id=record_id, investigation_id=acc, quantity=quantity,
                     value=value, unit=unit, value_status=status, source_column=col, source_file=src_file, source_row=src_row))


def iso(d, fmts=("%m/%d/%Y", "%m/%d/%y")):
    for f in fmts:
        try: return datetime.strptime(d.strip(), f).strftime("%Y-%m-%d")
        except Exception: pass
    return ""


def num_or_missing(s):
    s = (s or "").strip()
    if s in ("", "–", "-", "n/a", "none", "?"): return None
    return first_num(s)


def base(acc, r, i, hdr, rid):
    return dict(record_id=rid, investigation_id=acc, investigation=INVESTIGATIONS[acc]["acronym"],
                source_file=rel(table_path(acc)), source_row=i + 1,
                source_record=json.dumps(dict(zip(hdr, r)), ensure_ascii=False))


def rows_of(acc):
    t = read_csv_rows(table_path(acc))
    return t[0], t[1:]


def check_range(rec, field, lo, hi, rule):
    v = rec.get(field)
    if v is None or v == "": return
    if not (lo <= float(v) <= hi):
        rec["quality_notes"].append(f"{field}={v} outside [{lo},{hi}]; set to missing (original kept in source_record)")
        rec[field] = None
        Q.add(rec["source_record"], rec["source_file"], rec["investigation"], rec["record_id"],
              f"{field}={v} outside plausible range [{lo},{hi}]", rule, "warn")


def finish(rec):
    rec["quality_status"] = "warning" if rec["quality_notes"] else "valid"
    rec["quality_notes"] = "; ".join(rec["quality_notes"])
    return rec


# ---------------------------------------------------------------- BASS-II (PSI-25)
def bass2_outcome(air, fan):
    t = f"{air} | {fan}".lower()
    if "no ign" in t or "would not stay lit" in t: return "No Ignition", "observed"
    if "blowoff" in t or "out at fan" in t: return "Blowoff", "observed"
    if "ext" in t or re.search(r"\bout\b", t): return "Extinction", "observed"
    if re.search(r"\boff\b", t): return "Extinction", "observed"
    if not air.strip(): return "Unknown", "not_recorded"
    return "Burned", "inferred"   # NASA note lists flows only; no extinction/blowoff written


def air_flows(air):
    a = (air or "").lower().replace("<1", "0.5")
    a = re.sub(r"\(.*?\)", " ", a); a = re.sub(r"pots?\s*[\d.\s]+", " ", a)
    return [v for v in nums(a) if v <= 40]


def silver_bass2():
    acc = "PSI-25"; hdr, rows = rows_of(acc); out = []; seen = Counter()
    for i, r in enumerate(rows, start=1):
        if len(r) < 13 or not r[1]:
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "BASS-II", "", "row has no test number / too few columns", "required:test_id"); continue
        seen[r[1]] += 1
        rid = f"BASS-II-{r[1]}" + (f"-{seen[r[1]]}" if seen[r[1]] > 1 else "")
        rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        mid, c, dims, geo = add_sample(rid, acc, r[5], rec["source_file"], rec["source_row"])
        flows = air_flows(r[8]); oc, ob = bass2_outcome(r[8], r[7])
        rec.update(pi=r[0], test_number=r[1], test_date=iso(r[2]), test_date_raw=r[2], sample_number=r[4],
                   material_id=mid, material_original_name=r[5], material_family=c["material_family"], candidate_family=c["candidate_family"],
                   classification_basis=c["classification_basis"], geometry=geo,
                   thickness_mm=dims.get("thickness", (None,))[0], diameter_mm=dims.get("diameter", (None,))[0],
                   gravity_g=0.0, gravity_status="observed (ISS)",
                   o2_initial_pct=num_or_missing(r[11]), o2_final_pct=num_or_missing(r[12]),
                   co2_initial_pct=num_or_missing(r[13]), co2_final_pct=num_or_missing(r[14]),
                   co_initial_ppm=num_or_missing(r[15]), co_final_ppm=num_or_missing(r[16]),
                   pressure_kpa=ISS_KPA, pressure_status="assumed (ISS cabin; not in NASA table)",
                   flow_start_cm_s=flows[0] if flows else None, flow_min_cm_s=min(flows) if flows else None,
                   flow_status="observed (air display)" if flows else "missing",
                   air_display_raw=r[8], fan_display_raw=r[7], outcome_class=oc, outcome_basis=ob)
        check_range(rec, "o2_initial_pct", 10, 40, "range:o2_pct")
        check_range(rec, "o2_final_pct", 10, 40, "range:o2_pct")
        if rec["o2_initial_pct"] is not None and rec["o2_final_pct"] is not None and rec["o2_initial_pct"] - rec["o2_final_pct"] > 5:
            rec["quality_notes"].append("final O2 drops >5 points vs initial (possible transcription error)")
            Q.add(rec["source_record"], rec["source_file"], "BASS-II", rid, "final O2 more than 5 points below initial", "consistency:o2_drop", "warn")
        if c["classification_basis"] != "explicit_name":
            rec["quality_notes"].append("material not named in NASA table")
        for q_, col, u in [("o2_initial_pct", 11, "%vol"), ("o2_final_pct", 12, "%vol"), ("co2_initial_pct", 13, "%vol"),
                           ("co2_final_pct", 14, "%vol"), ("co_initial_ppm", 15, "ppm"), ("co_final_ppm", 16, "ppm")]:
            meas(rid, acc, q_, rec[q_], u, "observed", hdr[col], rec["source_file"], rec["source_row"])
        for k, f in enumerate(flows):
            meas(rid, acc, f"air_flow_step_{k+1}", f, "cm/s", "observed (air display)", hdr[8], rec["source_file"], rec["source_row"])
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- BASS (PSI-26)
def silver_bass():
    acc = "PSI-26"; hdr, rows = rows_of(acc); out = []; seen = Counter()
    for i, r in enumerate(rows, start=1):
        if len(r) < 6 or not r[3]:
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "BASS", "", "row has no test number", "required:test_id"); continue
        seen[r[3]] += 1
        rid = f"BASS-{r[3]}" + (f"-{seen[r[3]]}" if seen[r[3]] > 1 else "")
        rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        mid, c, dims, geo = add_sample(rid, acc, r[5], rec["source_file"], rec["source_row"])
        rec.update(test_date=iso(r[0]), test_date_raw=r[0], as_run_test_number=r[2], test_number=r[3], sample_number=r[4],
                   material_id=mid, material_original_name=r[5], material_family=c["material_family"], candidate_family=c["candidate_family"],
                   classification_basis=c["classification_basis"], geometry=geo, diameter_mm=dims.get("diameter", (None,))[0],
                   gravity_g=0.0, pressure_kpa=ISS_KPA, pressure_status="assumed (ISS cabin; not in NASA table)",
                   o2_status="missing (not in NASA table; see BASS papers)", flow_status="missing",
                   outcome_class="Unknown", outcome_basis="not_recorded")
        if c["classification_basis"] != "explicit_name": rec["quality_notes"].append("material not named in NASA table")
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- SAFFIRE-I/II/III
def silver_saffire(acc):
    hdr, rows = rows_of(acc); inv = INVESTIGATIONS[acc]["acronym"]; h = [x.lower() for x in hdr]; out = []
    gi = lambda key: next((k for k, x in enumerate(h) if key in x), None)
    get = lambda r, key: (r[gi(key)] if gi(key) is not None and gi(key) < len(r) else "")
    last_mat = ""
    for i, r in enumerate(rows, start=1):
        if not r or not re.match(r"^(S\d|\d-\d)", r[0]):
            if any(r): Q.add(dict(zip(hdr, r)), rel(table_path(acc)), inv, r[0] if r else "",
                             "not a sample row (e.g. pre-test flow visualization reference)", "required:sample_row", "info")
            continue
        rid = f"{inv}-{r[0]}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        mat = get(r, "material")
        if not mat:
            mat = last_mat; rec["quality_notes"].append("material cell empty; carried from previous row (NASA table layout)")
        last_mat = mat
        thick_cell = get(r, "thickness")
        th = first_num(thick_cell)
        if th is not None and "cm" in (thick_cell + hdr[gi("thickness")]).lower(): th = th * 10
        if re.match(r"\s*0\d", thick_cell or ""): th = float("0." + re.match(r"\s*0(\d+)", thick_cell).group(1))
        mid, c, dims, geo = add_sample(rid, acc, mat, rec["source_file"], rec["source_row"],
                                       extra={"thickness": (th, "mm"), "length": (first_num(get(r, "length")), "cm"),
                                              "width": (first_num(get(r, "width")), "cm")})
        bt, ugb = get(r, "burn time"), get(r, "-g burn length")
        if "insignificant" in bt.lower() or ugb.startswith("~ 0"): oc, ob = "Not Sustained", "observed"
        elif bt or ugb: oc, ob = "Burned", "observed"
        else: oc, ob = "Unknown", "not_recorded"
        rec.update(sample_number=r[0], material_id=mid, material_original_name=mat, material_family=c["material_family"],
                   candidate_family=c["candidate_family"], classification_basis=c["classification_basis"], geometry=geo or "sheet",
                   thickness_mm=th, length_cm=first_num(get(r, "length")), width_cm=first_num(get(r, "width")),
                   gravity_g=0.0, o2_initial_pct=first_num(get(r, "o2")), o2_status="observed" if get(r, "o2") else "missing",
                   o2_raw=get(r, "o2"), pressure_kpa=ISS_KPA, pressure_status="assumed (Cygnus cabin ~ISS; not in NASA table)",
                   flow_cm_s=first_num(get(r, "air flow")), flow_direction=get(r, "direction").strip(),
                   ignition_power_w=first_num(get(r, "ignition power")), ignition_time_s=first_num(get(r, "ignition time")),
                   burn_time_s=first_num(bt), burn_time_raw=bt, ug_burn_length_raw=ugb, one_g_burn_length_raw=get(r, "1-g burn length"),
                   one_g_spread_rate_raw=get(r, "1-g spread"), outcome_class=oc, outcome_basis=ob)
        check_range(rec, "o2_initial_pct", 10, 40, "range:o2_pct")
        for q_, u in [("o2_initial_pct", "%vol"), ("flow_cm_s", "cm/s"), ("burn_time_s", "s"), ("ignition_power_w", "W"), ("ignition_time_s", "s")]:
            meas(rid, acc, q_, rec[q_], u, "observed", q_, rec["source_file"], rec["source_row"])
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- SAME (PSI-102)
def silver_same():
    acc = "PSI-102"; hdr, rows = rows_of(acc); out = []
    for i, r in enumerate(rows, start=1):
        if not r or not r[0]: continue
        rid = f"SAME-{r[0]}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        name = r[1].split(":")[0].strip()
        mid, c, _, _ = add_sample(rid, acc, name, rec["source_file"], rec["source_row"])
        partial = ":" in r[1]
        if partial: rec["quality_notes"].append("NASA row says 'same conditions as 1-4'; numeric values not repeated (left missing, not copied)")
        rec.update(sample_number=r[0], material_id=mid, material_original_name=r[1], material_family=c["material_family"],
                   flow_cm_s=num_or_missing(r[2]) if len(r) > 2 else None, weight_loss_rate_mg_min=num_or_missing(r[3]) if len(r) > 3 else None,
                   aging_duration_min=num_or_missing(r[4]) if len(r) > 4 else None, gravity_g=0.0,
                   pressure_kpa=ISS_KPA, pressure_status="assumed (ISS cabin)", test_type="smoke generation (heated, not burned)",
                   outcome_class="Not a flame test", outcome_basis="not_applicable")
        for q_, u in [("flow_cm_s", "cm/s"), ("weight_loss_rate_mg_min", "mg/min"), ("aging_duration_min", "min")]:
            meas(rid, acc, q_, rec[q_], u, "observed", q_, rec["source_file"], rec["source_row"])
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- SAME-R (PSI-101)
def silver_same_r():
    acc = "PSI-101"; hdr, rows = rows_of(acc); out = []; seen = Counter()
    for i, r in enumerate(rows, start=1):
        if not r or not r[1]:
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "SAME-R", "", "row has no SAME test number", "required:test_id"); continue
        seen[(r[0], r[1])] += 1
        rid = f"SAME-R-{slug(r[0])}-{r[1]}" + (f"-{seen[(r[0], r[1])]}" if seen[(r[0], r[1])] > 1 else "")
        rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        mid, c, _, _ = add_sample(rid, acc, r[0], rec["source_file"], rec["source_row"])
        aged = bool(re.match(r"^\d+a$", r[1]))
        rec.update(material_id=mid, material_original_name=r[0], material_family=c["material_family"], same_test_number=r[1],
                   parent_test_number=r[1][:-1] if aged else "", is_aged_measurement=aged, description=r[2],
                   date_raw=r[3], date_status="partial (day-month only; year not in NASA table)",
                   inlet_velocity_cm_s=num_or_missing(r[4]), heater_resistance_ratio=num_or_missing(r[5]),
                   duration_s=num_or_missing(r[6]), primary_aging_time_s=num_or_missing(r[7]),
                   primary_mixing_time_s=num_or_missing(r[8]), net_aging_time_s=num_or_missing(r[9]),
                   gravity_g=0.0, pressure_kpa=ISS_KPA, pressure_status="assumed (ISS cabin)",
                   test_type="smoke generation (heated, not burned)", outcome_class="Not a flame test", outcome_basis="not_applicable")
        for q_, col, u in [("inlet_velocity_cm_s", 4, "cm/s"), ("heater_resistance_ratio", 5, "ratio Rt/R0"), ("duration_s", 6, "s"),
                           ("primary_aging_time_s", 7, "s"), ("primary_mixing_time_s", 8, "s"), ("net_aging_time_s", 9, "s")]:
            meas(rid, acc, q_, rec[q_], u, "observed", hdr[col], rec["source_file"], rec["source_row"])
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- FLEX (PSI-69)
FLEX_END = {"extinction": "Extinction", "disruption": "Disruption", "completion": "Burned"}


def silver_flex():
    acc = "PSI-69"; hdr, rows = rows_of(acc); out = []
    for i, r in enumerate(rows, start=1):
        if len(r) < 15 or not r[0]:
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "FLEX", "", "row has no FLEX test number", "required:test_id"); continue
        rid = f"FLEX-{r[0]}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        mid, c, _, _ = add_sample(rid, acc, r[4], rec["source_file"], rec["source_row"], kind="liquid_fuel")
        p_mm = num_or_missing(r[5]); fr = [num_or_missing(x) for x in r[6:10]]
        rec.update(flex_test_number=r[0], flex_identifier=r[1], test_date=iso(r[2]), test_date_raw=r[2], test_gmt=r[3],
                   fuel=r[4], material_id=mid, material_family=c["material_family"],
                   pressure_mmhg=p_mm, pressure_kpa=round(p_mm * MMHG_TO_KPA, 2) if p_mm is not None else None, pressure_status="observed",
                   # NASA header lost subscripts: "O"=O2, "N"=N2, "CO"=CO2, "He"=He (mole fractions). Converted to %.
                   o2_pct=round(fr[0] * 100, 2) if fr[0] is not None else None, n2_pct=round(fr[1] * 100, 2) if fr[1] is not None else None,
                   co2_pct=round(fr[2] * 100, 2) if fr[2] is not None else None, he_pct=round(fr[3] * 100, 2) if fr[3] is not None else None,
                   diluent_note="header subscripts restored (O->O2, N->N2, CO->CO2); see DATA_DICTIONARY",
                   droplet_initial_diameter_mm=num_or_missing(r[10]), extinction_diameter_mm=num_or_missing(r[11]),
                   burning_rate_as_labeled=num_or_missing(r[12]), burning_rate_unit_as_labeled="mm (as labeled by NASA; burning-rate constants are usually mm^2/s — unit not changed)",
                   burn_time_s=num_or_missing(r[13]), test_end_raw=r[14], gravity_g=0.0,
                   outcome_class=FLEX_END.get(r[14].strip().lower(), "Unknown"), outcome_basis="observed" if r[14].strip() else "not_recorded")
        s = sum(x for x in fr if x is not None)
        if fr[0] is not None and abs(s - 1) > 0.02:
            rec["quality_notes"].append(f"gas mole fractions sum to {round(s, 3)} (expected 1)")
            Q.add(rec["source_record"], rec["source_file"], "FLEX", rid, f"mole fractions sum {round(s, 3)}", "consistency:mole_fraction_sum", "warn")
        if not rec["test_date"]: rec["quality_notes"].append("test date missing/unparseable")
        if any(x == "–" for x in r): rec["quality_notes"].append("NASA marked some values with '–' (treated as missing)")
        check_range(rec, "pressure_kpa", 10, 400, "range:pressure_kpa")
        for q_, u in [("pressure_kpa", "kPa"), ("o2_pct", "%mol"), ("n2_pct", "%mol"), ("co2_pct", "%mol"), ("he_pct", "%mol"),
                      ("droplet_initial_diameter_mm", "mm"), ("extinction_diameter_mm", "mm"), ("burning_rate_as_labeled", "mm (as labeled)"), ("burn_time_s", "s")]:
            meas(rid, acc, q_, rec[q_], u, "observed" if q_ != "pressure_kpa" else "derived (mmHg x 0.133322)", q_, rec["source_file"], rec["source_row"])
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- CFI (PSI-39): one row per droplet test, conditions only
ATM_TO_KPA = 101.325


def silver_cfi():
    """Cool Flames Investigation. NASA's table gives pressure (as 'N atm'), O2/N2/He mole fractions, fiber yes/no and fuel.
    It has NO outcome column, so outcome_class=Unknown / outcome_basis=not_recorded (never inferred)."""
    acc = "PSI-39"; hdr, rows = rows_of(acc); out = []; seen = {}
    for i, r in enumerate(rows, start=1):
        if len(r) < 10 or not r[0]:
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "CFI", "", "row has no test number", "required:test_id"); continue
        key = tuple(x.strip() for x in r)
        if key in seen:  # NASA table repeats rows 24-31 as rows 81-88, field for field: keep first, quarantine the copy
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "CFI", f"CFI-{r[0]}",
                  f"exact duplicate of source row {seen[key]} (not loaded twice)", "duplicate:exact_row", "warn"); continue
        seen[key] = i + 1
        rid = f"CFI-{r[0]}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        mid, c, _, _ = add_sample(rid, acc, r[9], rec["source_file"], rec["source_row"], kind="liquid_fuel")
        m = re.match(r"\s*([\d.]+)\s*atm", r[4])
        p_atm = float(m.group(1)) if m else None
        fr = [num_or_missing(x) for x in r[5:8]]
        rec.update(cfi_test_number=r[0], test_date=iso(r[1], ("%d-%b-%y",)), test_date_raw=r[1], local_time=r[2].strip(), cir_identifier=r[3],
                   pressure_atm=p_atm, pressure_kpa=round(p_atm * ATM_TO_KPA, 1) if p_atm is not None else None,
                   pressure_status="observed (NASA table, atm)",
                   o2_pct=round(fr[0] * 100, 2) if fr[0] is not None else None, n2_pct=round(fr[1] * 100, 2) if fr[1] is not None else None,
                   he_pct=round(fr[2] * 100, 2) if fr[2] is not None else None,
                   fiber_supported={"yes": True, "no": False}.get(r[8].strip().lower()), fuel=r[9].strip(),
                   material_id=mid, material_family=c["material_family"], gravity_g=0.0,
                   outcome_class="Unknown", outcome_basis="not_recorded")
        if p_atm is None:
            rec["quality_notes"].append("pressure not parseable as 'N atm'")
            Q.add(rec["source_record"], rec["source_file"], "CFI", rid, f"pressure '{r[4]}' not parseable", "parse:pressure", "warn")
        s = sum(x for x in fr if x is not None)
        if fr[0] is not None and abs(s - 1) > 0.02:
            rec["quality_notes"].append(f"gas mole fractions sum to {round(s, 3)} (expected 1)")
            Q.add(rec["source_record"], rec["source_file"], "CFI", rid, f"mole fractions sum {round(s, 3)}", "consistency:mole_fraction_sum", "warn")
        if not rec["test_date"]: rec["quality_notes"].append("test date missing/unparseable")
        check_range(rec, "pressure_kpa", 10, 600, "range:pressure_kpa")
        for q_, u in [("pressure_kpa", "kPa"), ("o2_pct", "%mol"), ("n2_pct", "%mol"), ("he_pct", "%mol")]:
            meas(rid, acc, q_, rec[q_], u, "observed" if q_ != "pressure_kpa" else "derived (atm x 101.325)", q_, rec["source_file"], rec["source_row"])
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- FLEX-2 (PSI-68): test MATRIX, not individual tests
def _num_list(s):
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s or "")]


def silver_flex2():
    """FLEX-2's PSI table has one row per FUEL with the RANGE of conditions run (lists like '0.17; 0.21;0.25; 0.3').
    Kept as a test matrix: no per-test conditions or outcomes, so these rows are never counted as tests."""
    acc = "PSI-68"; hdr, rows = rows_of(acc); out = []
    for i, r in enumerate(rows, start=1):
        if len(r) < 7 or not r[0]:
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "FLEX-2", "", "row has no fuel", "required:fuel"); continue
        rid = f"FLEX2-m{i:02d}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        o2 = _num_list(r[3]); p = _num_list(r[4]); dia = _num_list(r[1]); flow = _num_list(r[6])
        rec.update(row_type="test matrix (condition ranges for this fuel; not an individual test)", fuel=r[0].strip(),
                   gas_mixtures=r[2].strip(), o2_levels_pct="; ".join(f"{x * 100:g}" for x in o2),
                   o2_min_pct=min(o2) * 100 if o2 else None, o2_max_pct=max(o2) * 100 if o2 else None,
                   pressure_levels_atm="; ".join(f"{x:g}" for x in p),
                   pressure_min_kpa=round(min(p) * ATM_TO_KPA, 1) if p else None, pressure_max_kpa=round(max(p) * ATM_TO_KPA, 1) if p else None,
                   droplet_diameter_min_mm=min(dia) if dia else None, droplet_diameter_max_mm=max(dia) if dia else None,
                   ambient_temperature_c=num_or_missing(r[5]), flow_min_cm_s=min(flow) if flow else None, flow_max_cm_s=max(flow) if flow else None,
                   gravity_g=0.0)
        if not o2 or not p:
            rec["quality_notes"].append("condition lists not parseable")
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- ACME (PSI-159, PSI-10, PSI-20): gaseous flames, ISS CIR
BAR_TO_KPA = 100.0


def _acme_tables(acc):
    """Main table + extra tables (normal and inverse flame files) as (path, header, rows)."""
    m = INVESTIGATIONS[acc]
    out = []
    for name in [m["table"]] + m.get("extra_tables", []):
        p = PSI / m["folder"] / "Experimental table" / name
        t = read_csv_rows(p)
        out.append((p, [h.strip() for h in t[0]], t[1:]))
    return out


def _col(hdr, row, *names):
    """Value of the first header that matches one of names (case/space-insensitive)."""
    norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
    for n in names:
        for i, h in enumerate(hdr):
            if norm(h) == norm(n) and i < len(row):
                return row[i].strip()
    return ""


CFIG_END = {"se": "Extinction", "ft": "Burned"}  # SE = self-extinguished; FT = flow terminated while still burning


def silver_acme_cfig():
    """ACME CFI-G: one row per test with NASA's outcome codes (Hot ignition yes/no; SE self-extinguished / FT flow terminated).
    861 fully blank rows in the inverse-flame file are not records and are skipped (counted in a quarantine info row)."""
    acc = "PSI-159"; out = []
    for path, hdr, rows in _acme_tables(acc):
        blank = 0
        for i, r in enumerate(rows, start=1):
            if not any(c.strip() for c in r):
                blank += 1; continue
            test = _col(hdr, r, "Test")
            if not test:
                Q.add(dict(zip(hdr, r)), rel(path), "ACME CFI-G", "", "row has no test id", "required:test_id"); continue
            ftype = _col(hdr, r, "Flame Type")
            rid = f"CFIG-{ftype[:1].upper()}-{test.replace(' ', '')}"
            rec = dict(record_id=rid, investigation_id=acc, investigation="ACME CFI-G", source_file=rel(path), source_row=i + 1,
                       source_record=json.dumps(dict(zip(hdr, r)), ensure_ascii=False), quality_notes=[])
            fuel = _col(hdr, r, "Fuel")
            mid, c, _, _ = add_sample(rid, acc, fuel, rec["source_file"], rec["source_row"], kind="gas_fuel")
            xo2 = num_or_missing(_col(hdr, r, "XO2", "XO2 before test"))
            p_bar = num_or_missing(_col(hdr, r, "approx p (bar)"))
            end = _col(hdr, r, "Self -ext or flow term", "Self-ext or flow term")
            bt = num_or_missing(_col(hdr, r, "burn time (sec)"))
            comment = _col(hdr, r, "Comments").lower()
            # 'Hot ignition' is NOT used: rows with 'No' still have burn times, FT/SE codes and comments like 'hot flame'.
            if end.lower() in CFIG_END:
                oc, ob = CFIG_END[end.lower()], "observed"
            elif bt == 0 or "fail" in comment:
                oc, ob = "No Ignition", "observed"
            else:
                oc, ob = "Unknown", "not_recorded"
            rec.update(flame_type=ftype, test=test, day=_col(hdr, r, "Day"), fuel=fuel, material_id=mid, material_family=c["material_family"],
                       o2_pct=round(xo2 * 100, 2) if xo2 is not None else None, o2_status="observed (XO2 before test)",
                       pressure_bar=p_bar, pressure_kpa=round(p_bar * BAR_TO_KPA, 1) if p_bar is not None else None,
                       pressure_status="approximate (NASA: approx p)", hot_ignition_raw=_col(hdr, r, "Hot ignition"),
                       test_end_raw=end, burn_time_s=num_or_missing(_col(hdr, r, "burn time (sec)")),
                       cool_flame_raw=_col(hdr, r, "Cool flame?", "TFP"), comments=_col(hdr, r, "Comments"),
                       gravity_g=0.0, outcome_class=oc, outcome_basis=ob)
            check_range(rec, "o2_pct", 0, 100, "range:o2_pct")
            check_range(rec, "pressure_kpa", 10, 600, "range:pressure_kpa")
            out.append(finish(rec))
        if blank:
            Q.add({"blank_rows": blank}, rel(path), "ACME CFI-G", "", f"{blank} fully blank rows in NASA file (not records; skipped)",
                  "format:blank_rows", "info")
    return out


def silver_acme_flame_design():
    """ACME Flame Design: one row per test with O2 fraction and measured pressure (atm). No outcome column -> not_recorded.
    Rows marked RAMPED (conditions changed during the run) keep RAMPED fields as missing with a note."""
    acc = "PSI-10"; out = []
    for path, hdr, rows in _acme_tables(acc):
        for i, r in enumerate(rows, start=1):
            if not any(c.strip() for c in r): continue
            test = _col(hdr, r, "Test")
            if not test:
                Q.add(dict(zip(hdr, r)), rel(path), "ACME Flame Design", "", "row has no test id", "required:test_id"); continue
            ftype = _col(hdr, r, "Flame Type")
            rid = f"FD-{ftype[:1].upper()}-{test}"
            rec = dict(record_id=rid, investigation_id=acc, investigation="ACME Flame Design", source_file=rel(path), source_row=i + 1,
                       source_record=json.dumps(dict(zip(hdr, r)), ensure_ascii=False), quality_notes=[])
            fuel = _col(hdr, r, "Fuel") or "C2H4"
            mid, c, _, _ = add_sample(rid, acc, fuel, rec["source_file"], rec["source_row"], kind="gas_fuel")
            xo2 = num_or_missing(_col(hdr, r, "XO2", "XO2 (init)"))
            p_atm = num_or_missing(_col(hdr, r, "pmean (atm)"))
            if "RAMPED" in r:
                rec["quality_notes"].append("NASA marked some values RAMPED (changed during the test); those fields kept as missing")
            rec.update(flame_type=ftype, test=test, day=_col(hdr, r, "Day"), fuel=fuel, material_id=mid, material_family=c["material_family"],
                       o2_pct=round(xo2 * 100, 2) if xo2 is not None else None, o2_status="observed (XO2)",
                       pressure_atm=p_atm, pressure_kpa=round(p_atm * ATM_TO_KPA, 1) if p_atm is not None else None,
                       pressure_status="observed (pmean, atm)", adiabatic_flame_temp_k=num_or_missing(_col(hdr, r, "Tad (K)")),
                       gravity_g=0.0, outcome_class="Unknown", outcome_basis="not_recorded")
            check_range(rec, "o2_pct", 0, 100, "range:o2_pct")
            check_range(rec, "pressure_kpa", 10, 600, "range:pressure_kpa")
            out.append(finish(rec))
    return out


def silver_acme_bre():
    """ACME Burning Rate Emulator: one row per test DAY (not per test). NASA lists the approximate O2 levels of tests that
    ignited and how many ignited; chamber pressure was varied but is not in this table. Two cells read '3400%' / '2100%':
    clearly 34 and 21 written as percent of a percent; corrected with a quality note (raw kept in source_record)."""
    acc = "PSI-20"; hdr, rows = rows_of(acc); out = []
    for i, r in enumerate(rows, start=1):
        if not any(c.strip() for c in r): continue
        rid = f"BRE-d{i:02d}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        raw = _col(hdr, r, "Oxygen Conc (percent)")
        fixed = raw
        for bad, good in (("3400%", "34"), ("2100%", "21")):
            if bad in fixed:
                fixed = fixed.replace(bad, good)
                rec["quality_notes"].append(f"'{bad}' read as {good}% (typo in NASA table)")
                Q.add(rec["source_record"], rec["source_file"], "ACME BRE", rid, f"O2 cell '{raw}' read as {fixed}", "format:o2_percent_typo", "warn")
        levels = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", fixed)]
        rec.update(row_type="session summary (one test day; not individual tests)",
                   date=f"{_col(hdr, r, 'Year')} {_col(hdr, r, 'Month')} {_col(hdr, r, 'Date')}",
                   burner_size_mm=num_or_missing(_col(hdr, r, "Burner Size (mm)")), fuel=_col(hdr, r, "Fuel Bottle"),
                   o2_levels_ignited_pct="; ".join(f"{x:g}" for x in levels), o2_max_pct=max(levels) if levels else None,
                   flames_ignited=num_or_missing(_col(hdr, r, "Flames Ignited")),
                   pressure_status="varied; not given in NASA table", notes=_col(hdr, r, "Notes"), gravity_g=0.0)
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- Session logs / indexes (all remaining PSI tables)
SESSION_LOGS = ["PSI-21", "PSI-22", "PSI-23", "PSI-106", "PSI-142", "PSI-47"]


def silver_session_logs():
    """Tables that are not per-test data: one row per test day (flames ignited), a figure index, or sampling sessions.
    Loaded so that every PSI combustion table is in the pipeline; never counted as tests."""
    out = []
    for acc in SESSION_LOGS:
        hdr, rows = rows_of(acc)
        hdr = [h.strip().lstrip("﻿") for h in hdr]
        for i, r in enumerate(rows, start=1):
            if not any(c.strip() for c in r): continue
            rid = f"{acc}-r{i:02d}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
            atm = _col(hdr, r, "Atmosphere*", "Atmosphere")
            if re.search(r"with N[3-9]\b", atm):
                rec["quality_notes"].append(f"'{atm}' read as N2 (typo in NASA table)")
            rec.update(row_type={"figure_index": "figure index (data are in the linked paper)",
                                 "dust_sampling_sessions": "sampling session"}.get(INVESTIGATIONS[acc]["kind"], "session log (one test day; not individual tests)"),
                       date_or_day=_col(hdr, r, "Test Day", "Test Day*", "Test Date", "Actual Day", "Data ID"),
                       fuel=_col(hdr, r, "Fuel Bottle", "Fuel Type", "Sample Material"),
                       atmosphere=re.sub(r"with N[3-9]\b", "with N2", atm),
                       flames_ignited=num_or_missing(_col(hdr, r, "Flames ignited", "Flames Ignited", "Flames Ignited*")),
                       summary=" | ".join(f"{h}: {v.strip()}" for h, v in zip(hdr, r) if v.strip() and h.lower() != "notes")[:400],
                       gravity_g=0.0)
            out.append(finish(rec))
    return out


# ---------------------------------------------------------------- SPICE (PSI-107)
def silver_spice():
    acc = "PSI-107"; hdr, rows = rows_of(acc); out = []; first = {}
    for i, r in enumerate(rows, start=1):
        if len(r) < 9 or not r[3]:
            Q.add(dict(zip(hdr, r)), rel(table_path(acc)), "SPICE", "", "row missing fuel", "required:fuel"); continue
        rid = f"SPICE-r{i:04d}"; rec = base(acc, r, i, hdr, rid); rec["quality_notes"] = []
        mid, c, _, _ = add_sample(rid, acc, r[3], rec["source_file"], rec["source_row"], kind="gas_fuel")
        key = tuple(r)
        dup_of = first.setdefault(key, rid)
        rec.update(gmt_day_of_year=num_or_missing(r[0]), date_status="partial (day-of-year only; year not in NASA table)",
                   gmt_ignition=r[1], gmt_flame_off=r[2], fuel=r[3], material_id=mid, material_family=c["material_family"],
                   nozzle_diameter_mm=num_or_missing(r[4]), fuel_rate_sccm=num_or_missing(r[5]), fuel_rate_mg_s=num_or_missing(r[6]),
                   hc_fuel_rate_mg_s=num_or_missing(r[7]), air_velocity_cm_s=num_or_missing(r[8]), gravity_g=0.0,
                   pressure_kpa=ISS_KPA, pressure_status="assumed (ISS cabin)",
                   duplicate_of=dup_of if dup_of != rid else "")
        if dup_of != rid:
            rec["quality_notes"].append(f"exact duplicate of {dup_of} (kept; excluded from Gold aggregates)")
            Q.add(rec["source_record"], rec["source_file"], "SPICE", rid, f"exact duplicate of {dup_of}", "duplicate:exact_row", "warn")
        for q_, u in [("nozzle_diameter_mm", "mm"), ("fuel_rate_sccm", "sccm"), ("fuel_rate_mg_s", "mg/s"),
                      ("hc_fuel_rate_mg_s", "mg/s"), ("air_velocity_cm_s", "cm/s")]:
            meas(rid, acc, q_, rec[q_], u, "observed", q_, rec["source_file"], rec["source_row"])
        out.append(finish(rec))
    return out


# ---------------------------------------------------------------- run
def build():
    tables = {
        "bass2_tests": silver_bass2(), "bass_tests": silver_bass(),
        "saffire1_tests": silver_saffire("PSI-98"), "saffire2_tests": silver_saffire("PSI-99"), "saffire3_tests": silver_saffire("PSI-100"),
        "same_smoke_tests": silver_same(), "same_r_smoke_tests": silver_same_r(),
        "flex_droplet_tests": silver_flex(), "spice_flames": silver_spice(),
        "cfi_cool_flame_tests": silver_cfi(), "flex2_test_matrix": silver_flex2(),
        "acme_cfig_tests": silver_acme_cfig(), "acme_flame_design_tests": silver_acme_flame_design(),
        "acme_bre_sessions": silver_acme_bre(), "psi_session_logs": silver_session_logs(),
    }
    for name, rows in tables.items():
        fields = list(dict.fromkeys(k for r in rows for k in r))
        write_csv(SILVER / "investigations" / f"{name}.csv", rows, fields)
    mats = []
    for m in sorted(MATERIALS.values(), key=lambda x: x["material_id"]):
        mats.append({**m, "original_names": " | ".join(sorted(m["original_names"]))[:500],
                     "investigations": " | ".join(sorted(m["investigations"])), "source_reference": " | ".join(sorted(m["source_reference"])),
                     "material_description": ""})
    mfields = ["material_id", "material_normalized_name", "material_family", "candidate_family", "classification_basis",
               "classification_confidence", "physical_form", "chemical_name", "material_composition", "manufacturer",
               "material_description", "original_names", "investigations", "source_reference"]
    write_csv(SILVER / "materials" / "materials.csv", mats, mfields)
    write_csv(SILVER / "materials" / "material_samples.csv", SAMPLES)
    write_csv(SILVER / "materials" / "material_properties.csv", PROPS)
    write_csv(SILVER / "measurements" / "measurements.csv", MEAS)
    # data/curated/ (values transcribed from NASA NTRS papers) is NOT loaded: the challenge data scope is PSI only.
    write_csv(QUAR / "quarantine.csv", Q.rows, ["original_record", "source_file", "investigation", "record_id", "failure_reason",
                                                "validation_rule", "severity", "processed_at"])
    return tables, mats


if __name__ == "__main__":
    t, m = build()
    for k, v in t.items(): print(f"{k:22s} {len(v):4d} rows | warnings {sum(r['quality_status'] == 'warning' for r in v)}")
    print("materials", len(m), "| samples", len(SAMPLES), "| properties", len(PROPS), "| measurements", len(MEAS), "| quarantine", len(Q.rows))
