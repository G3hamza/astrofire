"""Free-text scenario -> structured scenario (rule-based, no AI, no network).

Temporary front end for the team's chatbot: the chatbot can call POST /api/scenario/parse, or produce the same
JSON itself and call POST /api/scenario directly. Contract of the returned dict:
  scenario:   {material, mission (iss|exploration|moon|mars|None), gravity_g, o2_pct, pressure_kpa, flow_cm_s}
  understood: [{field, value, text}]   what was read from the user's words (text = the words it came from)
  defaulted:  [{field, value, reason}]  what was NOT in the text and was filled in
  warnings:   [str]                     e.g. a material NASA never tested
Nothing is invented: every value is either read from the text, taken from a named mission preset, or a stated default.
"""
import re

from .engine import MISSIONS

# Words people use -> material family names used in the NASA tables
MATERIAL_ALIASES = [
    (r"\bnomex\b|\baramid\b", "Aramid fabric (Nomex)"),
    (r"\bpmma\b|\bacrylic\b|plexi ?glass|perspex", "PMMA (acrylic)"),
    (r"\bsibal\b|cotton[- ]?fiberglass|cotton[- ]?fibreglass", "Cotton-fiberglass (SIBAL)"),
    (r"\bultem\b|polyetherimide", "Polyetherimide (Ultem)"),
    (r"\bsilicone\b", "Silicone"),
    (r"\bwax\b|\bcandle\b", "Wax"),
]
MISSION_WORDS = [
    (r"\bmars\b|\bmartian\b", "mars"),
    (r"\bmoon\b|\blunar\b|artemis", "moon"),
    (r"exploration atmosphere|\bgateway\b|\borion\b|8\.2 ?psi", "exploration"),
    (r"\biss\b|space station|\bstation\b|\borbit\b", "iss"),
]
# Common cabin materials with NO solid space fire test in the NASA tables: recognised by name and reported honestly
UNTESTED_NAMES = (r"\b(kevlar|nylon|polyester|polyethylene|polycarbonate|polyurethane|velcro|foam|kapton|polyimide|teflon|ptfe|"
                  r"cotton|wool|paper|cardboard|rubber|wire insulation|carbon fiber|fiberglass)\b")
NUM = r"(\d+(?:\.\d+)?)"


def _find(pattern, text):
    m = re.search(pattern, text, re.I)
    return m


def parse(text: str, known_materials: list[str] | None = None) -> dict:
    t = " " + (text or "").strip() + " "
    understood, defaulted, warnings = [], [], []

    # --- material
    material = None
    for pat, fam in MATERIAL_ALIASES:
        m = _find(pat, t)
        if m:
            material = fam
            understood.append({"field": "material", "value": fam, "text": m.group(0).strip()})
            break
    if material is None and known_materials:
        for fam in known_materials:
            if fam.lower() in t.lower():
                material = fam
                understood.append({"field": "material", "value": fam, "text": fam})
                break
    if material is None and (m := _find(UNTESTED_NAMES, t)):
        material = m.group(1).strip().capitalize()
        understood.append({"field": "material", "value": material, "text": m.group(0).strip()})
        warnings.append(f"NASA has no solid space fire test of '{material}' in these tables; StarryNight will show the closest tests of other materials.")
    if material is None:
        m = (_find(r"\b(?:sample|piece|sheet|panel|cover|made) of ([a-z][a-z\-]{2,25})\b", t)
             or _find(r"\bmaterial\s*(?:is|:)?\s*([a-z][a-z\-]{2,25})\b", t))
        if m:
            material = m.group(1).strip()
            understood.append({"field": "material", "value": material, "text": m.group(0).strip()})
            warnings.append(f"'{material}' is not a material in the NASA space fire tables; StarryNight will show the closest tests of other materials.")
        else:
            material = "PMMA (acrylic)"
            defaulted.append({"field": "material", "value": material, "reason": "no material named; PMMA is NASA's reference material"})

    # --- mission preset
    mission = None
    for pat, key in MISSION_WORDS:
        m = _find(pat, t)
        if m:
            mission = key
            understood.append({"field": "mission", "value": MISSIONS[key]["name"], "text": m.group(0).strip()})
            break

    base = MISSIONS[mission] if mission else MISSIONS["iss"]
    vals = {"gravity_g": base["gravity_g"], "o2_pct": base["o2_pct"], "pressure_kpa": base["pressure_kpa"], "flow_cm_s": 5.0}
    explicit = set()

    # --- oxygen: "34% O2", "30 % oxygen", "oxygen at 30%", "O2 = 25"
    m = _find(NUM + r"\s*%\s*(?:o2|o₂|oxygen)", t) or _find(r"(?:o2|o₂|oxygen)\D{0,15}?" + NUM + r"\s*%?", t)
    if m:
        vals["o2_pct"] = float(m.group(1)); explicit.add("o2_pct")
        understood.append({"field": "o2_pct", "value": vals["o2_pct"], "text": m.group(0).strip()})

    # --- pressure, converted to kPa
    m = _find(NUM + r"\s*(kpa|hpa|psia|psi|atm|bar|mbar)\b", t)
    if m:
        v, unit = float(m.group(1)), m.group(2).lower()
        kpa = {"kpa": v, "hpa": v / 10, "mbar": v / 10, "psia": v * 6.89476, "psi": v * 6.89476, "atm": v * 101.325, "bar": v * 100}[unit]
        vals["pressure_kpa"] = round(kpa, 1); explicit.add("pressure_kpa")
        understood.append({"field": "pressure_kpa", "value": vals["pressure_kpa"], "text": m.group(0).strip()})

    # --- gravity: "0.38 g", "1/6 g", "microgravity", "earth gravity"
    m = _find(NUM + r"\s*g\b(?!\w)", t)
    if m and float(m.group(1)) <= 1.5:
        vals["gravity_g"] = float(m.group(1)); explicit.add("gravity_g")
        understood.append({"field": "gravity_g", "value": vals["gravity_g"], "text": m.group(0).strip()})
    elif _find(r"1/6\s*g", t):
        vals["gravity_g"] = 0.166; explicit.add("gravity_g")
        understood.append({"field": "gravity_g", "value": 0.166, "text": "1/6 g"})
    elif (m := _find(r"micro-?gravity|zero[- ]?g|weightless", t)):
        vals["gravity_g"] = 0.0; explicit.add("gravity_g")
        understood.append({"field": "gravity_g", "value": 0.0, "text": m.group(0).strip()})
    elif (m := _find(r"earth gravity|normal gravity|\b1 ?g\b", t)):
        vals["gravity_g"] = 1.0; explicit.add("gravity_g")
        understood.append({"field": "gravity_g", "value": 1.0, "text": m.group(0).strip()})

    # --- air flow, converted to cm/s
    m = _find(NUM + r"\s*(cm/s|mm/s|m/s)", t)
    if m:
        v, unit = float(m.group(1)), m.group(2).lower()
        vals["flow_cm_s"] = round({"cm/s": v, "mm/s": v / 10, "m/s": v * 100}[unit], 2); explicit.add("flow_cm_s")
        understood.append({"field": "flow_cm_s", "value": vals["flow_cm_s"], "text": m.group(0).strip()})
    elif (m := _find(r"still air|no (?:air ?)?flow|quiescent|fan(?:s)? off", t)):
        vals["flow_cm_s"] = 0.0; explicit.add("flow_cm_s")
        understood.append({"field": "flow_cm_s", "value": 0.0, "text": m.group(0).strip()})

    src = f"{MISSIONS[mission]['name']} preset" if mission else "ISS cabin (default)"
    for f in ("gravity_g", "o2_pct", "pressure_kpa"):
        if f not in explicit:
            defaulted.append({"field": f, "value": vals[f], "reason": f"not in the text; from {src}"})
    if "flow_cm_s" not in explicit:
        defaulted.append({"field": "flow_cm_s", "value": 5.0, "reason": "not in the text; typical cabin ventilation used by NASA tests"})

    # A mission plus explicit numbers that differ from it becomes a custom scenario (the API overrides numbers when mission is set)
    tol = {"gravity_g": 0.02, "o2_pct": 0.5, "pressure_kpa": 2.0}
    if mission and any(f in explicit and abs(vals[f] - MISSIONS[mission][f]) > tol[f] for f in tol):
        mission = None
    if not understood:
        warnings.append("No scenario details were recognised. Try e.g. 'Nomex on Mars at 34% oxygen and 8.2 psi'.")
    return {"scenario": {"material": material, "mission": mission, **vals},
            "understood": understood, "defaulted": defaulted, "warnings": warnings}
