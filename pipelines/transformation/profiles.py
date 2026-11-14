"""Investigation profiles: one record per PSI combustion investigation (Gold).

Answers the challenge's "summarize and display" list for every investigation:
objectives, fuels and sample shape/size, test conditions (oxygen, pressure, air flow), what varied and what
stayed the same between tests, sensors / measurement types, the data files NASA provides, and how it relates
to fire safety (pillar, relevance tier, hardware family).

Every field says where it came from (field_basis):
  nasa_text  - copied from NASA's PSI investigation.json (objective, hypothesis, approach, research impacts, hardware ...)
  computed   - computed by us from the Silver/Gold test tables (ranges, counts, varied/constant factors)
  keyword    - keyword match on NASA's own text (sensors); the matched phrase is kept as evidence
  curated    - team classification in data/curation/investigation_curation.csv, each row with a basis quoting
               the challenge text or PSI metadata

Writes gold/analytics/investigation_profiles.json (nested, read by the API) and investigation_profiles.csv (flat).
"""
import csv, json, re
from collections import Counter
from pipelines.common import SILVER, GOLD, PSI, ROOT, INVESTIGATIONS, write_csv, investigation_json, psi_url

CURATION = ROOT / "data" / "curation" / "investigation_curation.csv"
PILLARS = {"prevention", "detection", "suppression", "fundamental"}
TIERS = {"direct", "related", "background"}

FIELD_BASIS = {
    "title": "nasa_text", "objective": "nasa_text", "hypothesis": "nasa_text", "approach": "nasa_text",
    "research_impacts": "nasa_text", "hardware": "nasa_text", "flight_program": "nasa_text", "project_type": "nasa_text",
    "sub_research_area": "nasa_text", "start_date": "nasa_text", "end_date": "nasa_text", "doi": "nasa_text",
    "publications": "nasa_text", "data_files": "computed", "conditions": "computed", "varied_factors": "computed",
    "constant_factors": "computed", "not_recorded_factors": "computed", "outcomes": "computed", "records": "computed",
    "sensors": "keyword (video also from data_files)", "measured_quantities": "keyword", "pillar": "curated", "pillar_secondary": "curated", "relevance_tier": "curated",
    "hardware_family": "curated", "fuel_phase": "curated", "study_type": "curated", "partial_gravity_note": "curated",
}

# Sensor / measurement keywords searched in NASA's approach + objective + hypothesis text.
SENSORS = [
    ("Video / cameras", r"\bvideo|camera|imag(?:ing|ery)\b"),
    ("Color (RGB) imaging", r"\bcolou?r (?:camera|video|imag)|\bRGB\b|Nikon|NEF"),
    ("Infrared imaging", r"\binfrared|\bIR camera|\bIR imag"),
    ("Thermocouples", r"thermocouple"),
    ("Radiometers", r"radiometer"),
    ("Oxygen sensors", r"\bO2 sensor|oxygen sensor|oxygen (?:concentration )?measur"),
    ("CO2 / CO sensors", r"\bCO2 sensor|carbon dioxide sensor|\bCO sensor|carbon monoxide"),
    ("Particle counters / smoke detectors", r"P-Trak|DustTrak|particle count|smoke detector|ionization detector|photoelectric|aerosol (?:monitor|instrument)"),
    ("Thermophoretic samplers", r"thermophoretic"),
    ("Flow measurement", r"flow ?meter|flow rate|anemometer|flow velocity"),
    ("Pressure transducers", r"pressure transducer|pressure sensor"),
    ("Photodiodes / PMTs / chemiluminescence", r"photodiode|photomultiplier|\bPMT|chemiluminescen|OH\*|CH\*"),
    ("Spectroscopy / pyrometry", r"spectromet|spectroscop|pyrometr"),
    ("Electrical (ion current, voltage)", r"ion current|chemi-ion|electrode|voltage"),
    ("Mass / weight loss", r"mass loss|weight loss|load cell"),
]


# Measured quantities named in NASA's own text (what the tests measured, not how).
MEASURES = [
    ("Flame spread rate", r"spread rate|flame spread"),
    ("Flame size / shape / length", r"flame (?:size|shape|length|standoff)|flame structure"),
    ("Extinction / flammability limits", r"extinction|flammability limit|limiting oxygen|\bLOI\b|quench"),
    ("Ignition", r"ignition"),
    ("Burning rate / mass loss", r"burning rate|burn rate|mass loss|regression rate"),
    ("Droplet diameter history", r"droplet diameter|extinction diameter|droplet (?:burning|combustion)"),
    ("Smoke particle size", r"particle size|size distribution|particulate"),
    ("Soot", r"\bsoot"),
    ("Temperature", r"temperature"),
    ("Gas composition (O2, CO2, CO)", r"gas (?:composition|analy|sampl)|carbon monoxide|O2 sensor|CO2 sensor|oxygen sensor|oxygen (?:concentration )?measur"),
    ("Flame color / radiation", r"flame colou?r|radiat"),
]


def _rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(x):
    try:
        v = float(x)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def _text(s):
    s = (s or "").replace("\r", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


# --- which rows describe each investigation, and which columns are its test conditions -------------------------
# kind "num" -> numeric range; "cat" -> distinct values. Units are the units of the Gold/Silver column.
NUM, CAT = "num", "cat"
SOLID_FIELDS = {"Material (NASA name)": ("material_raw", CAT, ""), "Material family": ("material_family_effective", CAT, ""),
                "Sample geometry": ("geometry", CAT, ""), "Thickness": ("thickness_mm", NUM, "mm"), "Diameter": ("diameter_mm", NUM, "mm"),
                "Oxygen (initial)": ("o2_initial_pct", NUM, "% O2"), "Pressure": ("pressure_kpa", NUM, "kPa"),
                "Air flow (start)": ("flow_start_cm_s", NUM, "cm/s"), "Air flow (lowest)": ("flow_min_cm_s", NUM, "cm/s"),
                "Flow direction": ("flow_direction", CAT, ""), "Gravity": ("gravity_g", NUM, "g")}
DROPLET_FIELDS = {"Fuel": ("fuel", CAT, ""), "Oxygen": ("o2_pct", NUM, "% O2"), "Pressure": ("pressure_kpa", NUM, "kPa"),
                  "Diluent": ("diluent", CAT, ""), "CO2 in atmosphere": ("co2_pct", NUM, "%"), "Helium in atmosphere": ("he_pct", NUM, "%"),
                  "Droplet initial diameter": ("droplet_initial_diameter_mm", NUM, "mm")}
COOL_FIELDS = {"Fuel": ("fuel", CAT, ""), "Oxygen": ("o2_pct", NUM, "% O2"), "Pressure": ("pressure_kpa", NUM, "kPa"),
               "Diluent": ("diluent", CAT, ""), "Helium in atmosphere": ("he_pct", NUM, "%"), "Fiber-supported droplet": ("fiber_supported", CAT, "")}
GAS_FIELDS = {"Fuel": ("fuel", CAT, ""), "Flame type": ("flame_type", CAT, ""), "Oxygen": ("o2_pct", NUM, "% O2"),
              "Pressure": ("pressure_kpa", NUM, "kPa")}
JET_FIELDS = {"Fuel": ("fuel", CAT, ""), "Nozzle diameter": ("nozzle_diameter_mm", NUM, "mm"),
              "Fuel flow rate": ("fuel_rate_mg_s", NUM, "mg/s"), "Air co-flow velocity": ("air_velocity_cm_s", NUM, "cm/s")}
SMOKE_FIELDS = {"Material": ("material", CAT, ""), "Air flow": ("flow_cm_s", NUM, "cm/s"),
                "Heater resistance ratio (temperature setting)": ("heater_resistance_ratio", NUM, ""), "Aging time": ("aging_time_s", NUM, "s")}
FLEX2_FIELDS = {"Fuel": ("fuel", CAT, ""), "Gas mixtures": ("gas_mixtures", CAT, ""), "Oxygen (lowest)": ("o2_min_pct", NUM, "% O2"),
                "Oxygen (highest)": ("o2_max_pct", NUM, "% O2"), "Pressure (lowest)": ("pressure_min_kpa", NUM, "kPa"),
                "Pressure (highest)": ("pressure_max_kpa", NUM, "kPa"), "Droplet diameter (smallest)": ("droplet_diameter_min_mm", NUM, "mm"),
                "Droplet diameter (largest)": ("droplet_diameter_max_mm", NUM, "mm"), "Air flow (highest)": ("flow_max_cm_s", NUM, "cm/s")}
BRE_FIELDS = {"Fuel": ("fuel", CAT, ""), "Burner size": ("burner_size_mm", CAT, "mm"), "Highest oxygen ignited": ("o2_max_pct", NUM, "% O2")}
LOG_FIELDS = {"Fuel": ("fuel", CAT, ""), "Atmosphere": ("atmosphere", CAT, "")}


def _sources():
    """investigation_id -> (rows, fields, table description)."""
    g = GOLD / "analytics"; s = SILVER / "investigations"
    solids = _rows(g / "solid_fire_tests.csv")
    gas = _rows(g / "gas_flame_tests.csv")
    smoke = _rows(g / "smoke_generation_tests.csv")
    logs = _rows(s / "psi_session_logs.csv")
    out = {}
    for acc in ("PSI-25", "PSI-26", "PSI-98", "PSI-99", "PSI-100"):
        out[acc] = ([r for r in solids if r["investigation_id"] == acc], SOLID_FIELDS, "gold/analytics/solid_fire_tests.csv")
    out["PSI-69"] = (_rows(g / "droplet_extinction_tests.csv"), DROPLET_FIELDS, "gold/analytics/droplet_extinction_tests.csv")
    out["PSI-39"] = (_rows(g / "cool_flame_tests.csv"), COOL_FIELDS, "gold/analytics/cool_flame_tests.csv")
    out["PSI-159"] = ([r for r in gas if r["investigation"] == "ACME CFI-G"], GAS_FIELDS, "gold/analytics/gas_flame_tests.csv")
    out["PSI-10"] = ([r for r in gas if r["investigation"] == "ACME Flame Design"], GAS_FIELDS, "gold/analytics/gas_flame_tests.csv")
    out["PSI-107"] = (_rows(g / "gas_jet_flame_conditions.csv"), JET_FIELDS, "gold/analytics/gas_jet_flame_conditions.csv")
    out["PSI-102"] = ([r for r in smoke if r["investigation"] == "SAME"], SMOKE_FIELDS, "gold/analytics/smoke_generation_tests.csv")
    out["PSI-101"] = ([r for r in smoke if r["investigation"] == "SAME-R"], SMOKE_FIELDS, "gold/analytics/smoke_generation_tests.csv")
    out["PSI-68"] = (_rows(s / "flex2_test_matrix.csv"), FLEX2_FIELDS, "silver/investigations/flex2_test_matrix.csv")
    out["PSI-20"] = (_rows(s / "acme_bre_sessions.csv"), BRE_FIELDS, "silver/investigations/acme_bre_sessions.csv")
    for acc in ("PSI-21", "PSI-22", "PSI-23", "PSI-106", "PSI-142", "PSI-47"):
        out[acc] = ([r for r in logs if r["investigation_id"] == acc], LOG_FIELDS, "silver/investigations/psi_session_logs.csv")
    return out


def summarize(rows, fields):
    """Per condition: range or distinct values; and whether it varied, stayed constant, or was not recorded."""
    conds, varied, constant, missing = [], [], [], []
    for label, (col, kind, unit) in fields.items():
        vals = [r.get(col) for r in rows if r.get(col) not in (None, "")]
        if kind == NUM:
            nums = sorted({v for v in (_num(x) for x in vals) if v is not None})
            if not nums:
                missing.append(label); continue
            c = dict(factor=label, column=col, kind="range", unit=unit, min=nums[0], max=nums[-1], distinct=len(nums), records_with_value=len(vals))
        else:
            cnt = Counter(_text(v) for v in vals)
            if not cnt:
                missing.append(label); continue
            c = dict(factor=label, column=col, kind="values", unit=unit, values=[dict(value=k, records=n) for k, n in cnt.most_common(12)],
                     distinct=len(cnt), records_with_value=len(vals))
        conds.append(c)
        if c["distinct"] > 1:
            varied.append(label)
        else:
            constant.append(dict(factor=label, value=c.get("min") if kind == NUM else c["values"][0]["value"], unit=unit))
    return conds, varied, constant, missing


def outcomes(rows):
    if not rows or "outcome_class" not in rows[0]:
        return None
    return dict(by_class=dict(Counter(r["outcome_class"] or "not recorded" for r in rows).most_common()),
                by_basis=dict(Counter(r.get("outcome_basis") or "not recorded" for r in rows).most_common()))


def sensors(text, table=SENSORS):
    out = []
    for label, pat in table:
        m = re.search(pat, text, flags=re.I)
        if m:
            a, b = max(0, m.start() - 60), min(len(text), m.end() + 60)
            out.append(dict(sensor=label, evidence="..." + text[a:b].strip() + "..."))
    return out


def data_files(acc):
    """What NASA provides for download (PSI files manifest): file categories and file types."""
    p = PSI / INVESTIGATIONS[acc]["folder"] / "files_manifest.csv"
    if not p.exists():
        return None
    rows = _rows(p)
    cats = Counter((r["category"].split("/")[0].strip() or "Other") for r in rows)
    exts = Counter((r["file"].rsplit(".", 1)[-1].lower() if "." in r["file"] else "none") for r in rows)
    total = sum(_num(r["bytes"]) or 0 for r in rows)
    return dict(files=len(rows), total_gb=round(total / 1e9, 2), downloaded_here=sum(r["downloaded"] == "True" for r in rows),
                categories=dict(cats.most_common()), file_types=dict(exts.most_common(10)),
                has_video=any(e in exts for e in ("mp4", "avi", "mov", "mpg", "wmv")),
                has_images=any(e in exts for e in ("tif", "tiff", "jpg", "jpeg", "png", "bmp", "nef")))


def build():
    cur = {r["investigation_id"]: r for r in _rows(CURATION)}
    missing = set(INVESTIGATIONS) - set(cur)
    if missing:
        raise ValueError(f"investigation_curation.csv is missing {sorted(missing)}")
    for acc, c in cur.items():
        if c["pillar"] not in PILLARS or (c["pillar_secondary"] and c["pillar_secondary"] not in PILLARS) or c["relevance_tier"] not in TIERS:
            raise ValueError(f"bad curation values for {acc}: {c}")
    src = _sources()
    profiles, flat = [], []
    for acc, meta in INVESTIGATIONS.items():
        j = investigation_json(acc); c = cur[acc]
        rows, fields, table = src.get(acc, ([], {}, None))
        conds, varied, constant, notrec = summarize(rows, fields) if rows else ([], [], [], [])
        nasa = {k: _text(j.get(v)) for k, v in dict(title="title", objective="objective", hypothesis="hypothesis", approach="approach",
                                                     research_impacts="researchImpacts", hardware="experimentHardware",
                                                     flight_program="flightProgram", project_type="projectType",
                                                     sub_research_area="subResearchArea", start_date="investigationStartDate",
                                                     end_date="investigationEndDate", doi="doi").items()}
        pubs = [dict(title=_text(p.get("title")), authors=_text(p.get("authorList")), doi=_text(p.get("doi"))) for p in (j.get("publications") or [])]
        text = " ".join([nasa["approach"], nasa["objective"], nasa["hypothesis"]])
        sens = sensors(text)
        files = data_files(acc)
        have = {s["sensor"] for s in sens}
        if files and files["has_video"] and "Video / cameras" not in have:
            sens.append(dict(sensor="Video / cameras", evidence=f"{files['file_types'].get('mp4', 0) or 'some'} video files listed in the PSI file manifest", basis="data_files"))
        prof = dict(investigation_id=acc, acronym=meta["acronym"], **nasa, psi_url=psi_url(acc),
                    pillar=c["pillar"], pillar_secondary=c["pillar_secondary"] or None, relevance_tier=c["relevance_tier"],
                    hardware_family=c["hardware_family"], fuel_phase=c["fuel_phase"], study_type=c["study_type"],
                    partial_gravity_note=c["partial_gravity_note"] or None, curation_basis=c["curation_basis"],
                    records=len(rows), records_table=table, conditions=conds, varied_factors=varied, constant_factors=constant,
                    not_recorded_factors=notrec, outcomes=outcomes(rows), sensors=sens, measured_quantities=sensors(text, MEASURES),
                    publications_count=len(pubs), publications=pubs[:5], data_files=files, field_basis=FIELD_BASIS)
        profiles.append(prof)
        rng = {x["factor"]: x for x in conds if x["kind"] == "range"}
        o2 = [rng[k] for k in rng if k.startswith("Oxygen")]
        flat.append(dict(investigation_id=acc, acronym=meta["acronym"], title=nasa["title"], pillar=c["pillar"],
                         pillar_secondary=c["pillar_secondary"], relevance_tier=c["relevance_tier"], hardware_family=c["hardware_family"],
                         fuel_phase=c["fuel_phase"], study_type=c["study_type"], records=len(rows),
                         o2_min_pct=min((x["min"] for x in o2), default=""), o2_max_pct=max((x["max"] for x in o2), default=""),
                         varied_factors="; ".join(varied), sensors="; ".join(s["sensor"] for s in sens),
                         publications=len(pubs), data_files=(prof["data_files"] or {}).get("files", ""), psi_url=psi_url(acc)))
    order = {"direct": 0, "related": 1, "background": 2}
    profiles.sort(key=lambda p: (order[p["relevance_tier"]], p["acronym"]))
    flat.sort(key=lambda p: (order[p["relevance_tier"]], p["acronym"]))
    out = GOLD / "analytics" / "investigation_profiles.json"
    out.write_text(json.dumps(profiles, ensure_ascii=False, indent=1), encoding="utf-8")
    write_csv(GOLD / "analytics" / "investigation_profiles.csv", flat)
    return profiles


if __name__ == "__main__":
    for p in build():
        print(f"{p['investigation_id']:8s} {p['acronym']:28s} {p['relevance_tier']:10s} {p['pillar']:12s} rec={p['records']:4d} "
              f"varied={len(p['varied_factors'])} sensors={len(p['sensors'])} pubs={p['publications_count']}")
