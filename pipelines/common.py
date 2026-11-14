"""Shared helpers for the AstroFire data pipeline (Bronze -> Silver -> Gold).

Rules enforced here:
- Bronze (data/raw) is read-only. Nothing in this package writes to it.
- Every Silver/Gold record carries source_file + source_row (or chunk/document ids) for traceability.
- Values are tagged observed / inferred / assumed / missing. Nothing is invented.
"""
import csv, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRONZE = ROOT / "data" / "raw"            # Bronze layer = original downloads (kept at data/raw for compatibility)
PSI = BRONZE / "psi"
NTRS = BRONZE / "ntrs"
SILVER = ROOT / "data" / "silver"
GOLD = ROOT / "data" / "gold"
QUAR = ROOT / "data" / "quarantine"
MANIFESTS = ROOT / "data" / "manifests"
PROCESSED = ROOT / "data" / "processed"   # legacy folder the backend reads; regenerated from Gold
SCHEMAS = ROOT / "schemas"
DOCS = ROOT / "docs"

RUN_TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
ISS_KPA = 101.3

# Habitat design points: the ONE definition used by the pipeline (gold mission coverage) and the API (scenario, ranking).
# Moon/Mars/rover: 34% O2 at 56.5 kPa (8.2 psia, NASA exploration atmosphere), inside the challenge range
# ("30% or greater ... 10.2 psi [70.3 kPa] or less"). Spacecraft in transit: sea-level air like the ISS. Sources: docs/SOURCES.md.
# in_missions: shown in the existing 4-mission pickers (/api/missions); spacecraft and rover are ranking-only for now.
HABITATS = {
    "iss":         dict(name="ISS cabin", kind="space station", gravity_g=0.0, o2_pct=21.0, pressure_kpa=101.3, in_missions=True),
    "spacecraft":  dict(name="Crew spacecraft in transit", kind="spacecraft", gravity_g=0.0, o2_pct=21.0, pressure_kpa=101.3, in_missions=False),
    "exploration": dict(name="Exploration atmosphere (8.2 psia / 34% O2)", kind="spacecraft", gravity_g=0.0, o2_pct=34.0, pressure_kpa=56.5, in_missions=True),
    "moon":        dict(name="Lunar habitat", kind="lunar surface base", gravity_g=0.166, o2_pct=34.0, pressure_kpa=56.5, in_missions=True),
    "rover":       dict(name="Pressurized lunar rover", kind="pressurized rover", gravity_g=0.166, o2_pct=34.0, pressure_kpa=56.5, in_missions=False),
    "mars":        dict(name="Mars habitat", kind="Martian surface base", gravity_g=0.38, o2_pct=34.0, pressure_kpa=56.5, in_missions=True),
}
MMHG_TO_KPA = 0.133322

# Investigations in scope. role: primary = the 6 selected; supporting = already used by the engine.
INVESTIGATIONS = {
    "PSI-25":  dict(acronym="BASS-II",     folder="PSI-25_BASS-II",     table="PSI-25_Experimental table_BASS-II.csv",   role="primary",    kind="solid_flame_spread", platform="ISS MSG"),
    "PSI-69":  dict(acronym="FLEX",        folder="PSI-69_FLEX",        table="PSI-69_Experimental table_FLEX.csv",      role="primary",    kind="droplet_extinction", platform="ISS CIR"),
    "PSI-102": dict(acronym="SAME",        folder="PSI-102_SAME",       table="PSI-102_Experimental table_SAME.csv",     role="primary",    kind="smoke",              platform="ISS MSG"),
    "PSI-101": dict(acronym="SAME-R",      folder="PSI-101_SAME-R",     table="PSI-101_Experimental table_SAME-R.csv",   role="primary",    kind="smoke",              platform="ISS MSG"),
    "PSI-98":  dict(acronym="SAFFIRE-I",   folder="PSI-98_SAFFIRE-I",   table="PSI-98_Experimental table_SAFFIRE-1.csv", role="primary",    kind="solid_flame_spread", platform="Cygnus (uncrewed)"),
    "PSI-107": dict(acronym="SPICE",       folder="PSI-107_SPICE",      table="PSI-107_Experimental table_Spice.csv",    role="primary",    kind="gas_jet_flame",      platform="ISS MSG"),
    "PSI-26":  dict(acronym="BASS",        folder="PSI-26_BASS",        table="PSI-26_Experimental table_BASS.csv",      role="supporting", kind="solid_flame_spread", platform="ISS MSG"),
    "PSI-99":  dict(acronym="SAFFIRE-II",  folder="PSI-99_SAFFIRE-II",  table="PSI-99_Experimental table_SAFFIRE-2.csv", role="supporting", kind="solid_flame_spread", platform="Cygnus (uncrewed)"),
    "PSI-100": dict(acronym="SAFFIRE-III", folder="PSI-100_SAFFIRE-III",table="PSI-100_Experimental table_SAFFIRE-3.csv",role="supporting", kind="solid_flame_spread", platform="Cygnus (uncrewed)"),
    "PSI-39":  dict(acronym="CFI",         folder="PSI-39_CFI",         table="PSI-39_Experimental table_CFI.csv",       role="supporting", kind="droplet_cool_flame", platform="ISS CIR"),
    "PSI-68":  dict(acronym="FLEX-2",      folder="PSI-68_FLEX-2",      table="PSI-68_Experimental table_Flex2.csv",     role="supporting", kind="droplet_test_matrix", platform="ISS CIR"),
    # ACME gaseous flames in the ISS Combustion Integrated Rack: oxygen 12-85 %, 0.42-3.3 atm (see silver_acme_*)
    "PSI-159": dict(acronym="ACME CFI-G",   folder="PSI-159_ACME_CFI-G", table="PSI-159_Experimental table_CFI-G_Normal Flames.csv",
                    extra_tables=["PSI-159_Experimental table_CFI-G_Inverse Flames.csv"], role="supporting", kind="gas_flame", platform="ISS CIR"),
    "PSI-10":  dict(acronym="ACME Flame Design", folder="PSI-10_ACME-Flame_Design", table="PSI-10_Experimental table_Flame Design_Normal Flame.csv",
                    extra_tables=["PSI-10_Experimental table_Flame Design_Inverse Flame.csv"], role="supporting", kind="gas_flame", platform="ISS CIR"),
    "PSI-20":  dict(acronym="ACME BRE",    folder="PSI-20_ACME_BRE",    table="PSI-20_Experimental table_ACME BRE.csv",  role="supporting", kind="gas_flame_sessions", platform="ISS CIR"),
    # Session logs / indexes (one row per test day, figure list or sampling session): loaded into silver psi_session_logs
    "PSI-21":  dict(acronym="ACME CLD",      folder="PSI-21_ACME_CLD_Flame",      table="PSI-21_Experimental table_CLD Flame.csv",            role="reference", kind="gas_flame_sessions", platform="ISS CIR"),
    "PSI-22":  dict(acronym="ACME E-FIELD",  folder="PSI-22_ACME_E-FIELD_Flames", table="PSI-22_Experimental table_ACME E-FIELD Flames.csv",  role="reference", kind="gas_flame_sessions", platform="ISS CIR"),
    "PSI-23":  dict(acronym="ACME s-Flame",  folder="PSI-23_ACME_s-Flame",        table="PSI-23_Experimental table_ACME s-Flame.csv",         role="reference", kind="gas_flame_sessions", platform="ISS CIR"),
    "PSI-106": dict(acronym="SLICE",         folder="PSI-106_SLICE",              table="PSI-106_Experimental table_Slice.csv",               role="reference", kind="gas_flame_sessions", platform="ISS MSG"),
    "PSI-142": dict(acronym="Cool-flame counterflow study", folder="PSI-142_Quantitative_Studies_of_Cool_Flame_Trans", table="PSI-142_Experimental table_Data Summary Table.csv", role="reference", kind="figure_index", platform="n/a (ground analysis of FLEX data)"),
    "PSI-47":  dict(acronym="DAFT",          folder="PSI-47_DAFT_-_DAFT-2",       table="PSI-47_Experimental table_DAFT.csv",                 role="reference", kind="dust_sampling_sessions", platform="ISS"),
    # Analysis / modeling projects: PSI holds no data table for them
    "PSI-60":  dict(acronym="SPICE analysis", folder="PSI-60_Computational_and_Experimental_Analysis_", table=None, role="reference", kind="modeling", platform="n/a"),
    "PSI-115": dict(acronym="SAME data study", folder="PSI-115_Utilization_of_the_Smoke_Aerosol_Measure", table=None, role="reference", kind="modeling", platform="n/a"),
    "PSI-117": dict(acronym="Cool-flame CFD", folder="PSI-117_Effect_of_External_Thermo-Convective_Per", table=None, role="reference", kind="modeling", platform="n/a"),
    "PSI-62":  dict(acronym="BASS-Modeling", folder="PSI-62_Concurrent_Flame_Spread_Modeling_using_F", table=None, role="reference", kind="modeling", platform="n/a"),
}

OUTCOME_CLASSES = ["Burned", "Extinction", "Blowoff", "No Ignition", "Not Sustained", "Disruption", "Not a flame test", "Unknown"]
OUTCOME_BASIS = ["observed", "inferred", "not_recorded", "not_applicable"]


def table_path(acc):
    m = INVESTIGATIONS[acc]
    return PSI / m["folder"] / "Experimental table" / m["table"]


def rel(p):
    return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")


def read_csv_rows(path):
    """NASA tables mix UTF-8 and Windows-1252 bytes; decode strictly, fall back to cp1252 (no silent '?')."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    import io
    return [[c.strip() for c in r] for r in csv.reader(io.StringIO(text, newline=""))]


def write_csv(path, rows, fields=None):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0].keys()) if rows else [])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    try:  # Parquet copy for Gold/Silver consumers (Power BI, pandas). CSV stays the source of truth.
        import pandas as pd
        pd.DataFrame(rows, columns=fields).astype(str).replace({"None": ""}).to_parquet(path.with_suffix(".parquet"), index=False)
    except Exception:
        pass
    return path


def write_jsonl(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def sha256(path, block=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while (b := f.read(block)): h.update(b)
    return h.hexdigest()


def nums(s):
    return [float(x) for x in re.findall(r"\d*\.\d+|\d+", s or "")]


def first_num(s):
    n = nums(s)
    return n[0] if n else None


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:60] or "unknown"


def psi_url(acc):
    return f"https://psi.nasa.gov/physci/repo/data/investigations/{acc}"


def investigation_json(acc):
    p = PSI / INVESTIGATIONS[acc]["folder"] / "investigation.json"
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


class Quarantine:
    """Collects rejected/suspicious records. Nothing is silently dropped."""
    def __init__(self):
        self.rows = []

    def add(self, original, source_file, investigation, record_id, reason, rule, severity="reject"):
        self.rows.append(dict(original_record=json.dumps(original, ensure_ascii=False)[:2000], source_file=source_file,
                              investigation=investigation, record_id=record_id or "", failure_reason=reason,
                              validation_rule=rule, severity=severity, processed_at=RUN_TS))
