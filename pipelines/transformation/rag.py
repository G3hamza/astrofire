"""Gold knowledge base for the AI analyst: PSI-only documents + passages, every passage with provenance.

Replaces the earlier 307-paper NTRS collection (out of the challenge's data scope). Same files, same contract:
documents.jsonl : one line per document (document_id, title, investigation_id, kind, url, source_path, source_sha256)
chunks.jsonl    : one line per passage  (chunk_id, document_id, investigation_id, field, content_type, url,
                  source_path, text)  - content_type says what the text IS:
                    nasa_text            copied from NASA's PSI investigation.json (objective, hypothesis, approach, impacts)
                    computed_summary     computed by the pipeline from the Gold/Silver test tables (counts, ranges)
                    challenge_resource   the Space Apps 2026 challenge's own resources tab (Earth applications, incidents);
                                         background, never experimental evidence
Built from gold/analytics/investigation_profiles.json (built just before this step) and the Gold tables.
"""
import csv, json
from collections import Counter, defaultdict
from pipelines.common import GOLD, PSI, INVESTIGATIONS, write_jsonl, sha256, rel

SIZE = 900
CHALLENGE_URL = "https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/"
# The challenge's Resources tab (links given by the challenge). Text is a short neutral description of each page.
CHALLENGE_RESOURCES = [
    ("CR-spinoff-air-tanks", "Fireman's air tanks (NASA Spinoff)", "https://spinoff.nasa.gov/node/9582",
     "Earth application listed by the challenge: 1970s adaptation of spacesuit technology that improved firefighters' air tanks and breathing gear."),
    ("CR-spinoff-fire-detector", "Fire detector that tells smoke from dust (NASA Spinoff)", "https://spinoff.nasa.gov/node/9407",
     "Earth application listed by the challenge: a 1970s smoke detector developed for the Space Shuttle that discriminates between smoke and dust, "
     "giving fewer nuisance alarms; used in industry, for example mining."),
    ("CR-spinoff-fire-attire", "New technology for the fire attire (NASA Spinoff)", "https://spinoff.nasa.gov/node/9918",
     "Earth application listed by the challenge: a 1980s application of spacesuit technology that improved firefighter protective clothing."),
    ("CR-water-mist", "Fine-water-mist extinguishers (challenge text)", CHALLENGE_URL,
     "The challenge states that fine-water-mist extinguishers developed for use on the ISS have practical applications on Earth."),
    ("CR-apollo-1", "Apollo 1 fire (NASA Safety and Mission Assurance)", "https://sma.nasa.gov/sma-disciplines/accllp/apollo-1",
     "Listed by the challenge: in 1967 the Apollo 1 crew died in a pre-launch test when fire erupted in their oxygen-filled spacecraft."),
    ("CR-apollo-13", "Apollo 13 oxygen tank explosion (NASA Safety and Mission Assurance)", "https://sma.nasa.gov/sma-disciplines/accllp/apollo-13",
     "Listed by the challenge: the Apollo 13 crew survived an oxygen tank explosion on the way to the Moon."),
    ("CR-mir", "Fire aboard space station Mir, 1997 (NASA History)", "https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/",
     "Listed by the challenge: a multinational crew survived a fire aboard Mir caused by an oxygen generator failure."),
    ("CR-habitat-atmosphere", "Moon base atmosphere (challenge text)", CHALLENGE_URL,
     "The challenge states that the Moon base and pressurized rovers are expected to use an oxygen concentration of 30% or greater at a "
     "pressure of 10.2 psi (70.3 kPa) or less, between a spacesuit (100% O2 at 4.3 psi) and Earth air, which makes materials more flammable."),
    ("CR-partial-gravity", "Partial-gravity data status (challenge text)", CHALLENGE_URL,
     "The challenge states there is currently no partial-gravity combustion data in PSI; data is expected later from LUCI and FM2. "
     "E-FIELD Flames mimicked partial gravity with an electric field; microgravity and normal-gravity results could bound intermediate gravity."),
    ("CR-highest-oxygen", "Highest oxygen tested in microgravity (challenge text)", CHALLENGE_URL,
     "The challenge states that the microgravity tests with the highest oxygen concentrations were ACME's Cool Flames Investigation "
     "with Gases (CFI-G): the chamber held nitrogen and a flammable gas (e.g. propane) while an oxygen-nitrogen mixture of up to 85% oxygen "
     "flowed from a spherical burner, creating an inside-out flame."),
    ("CR-rockets-out-of-scope", "Rockets and propellants are out of scope (challenge text)", CHALLENGE_URL,
     "The challenge states that fire safety involving rockets and propellants is generally beyond the scope of PSI research."),
]


def _split(text):
    """Sentence-packing splitter: passages of about SIZE characters, never cutting a sentence."""
    out, buf = [], ""
    for s in text.replace("\n", " ").split(". "):
        s = s.strip()
        if not s: continue
        s = s if s.endswith(".") else s + "."
        if len(buf) + len(s) > SIZE and buf:
            out.append(buf.strip()); buf = ""
        buf += " " + s
    if buf.strip(): out.append(buf.strip())
    return out


def _rows(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _table_summaries():
    """investigation_id -> list of computed summary sentences from the Gold test tables."""
    out = defaultdict(list)
    solids = _rows(GOLD / "analytics" / "solid_fire_tests.csv")
    by = defaultdict(list)
    for r in solids: by[(r["investigation_id"], r["material_family_effective"])].append(r)
    for (inv, fam), rs in sorted(by.items()):
        oc = Counter(r["outcome_class"] for r in rs); basis = Counter(r["outcome_basis"] for r in rs)
        o2 = sorted(float(r["o2_initial_pct"]) for r in rs if r["o2_initial_pct"])
        fl = sorted(float(r["flow_min_cm_s"]) for r in rs if r["flow_min_cm_s"])
        out[inv].append(f"{len(rs)} solid-material space tests of {fam}: outcomes {dict(oc)}; outcome basis {dict(basis)} "
                        "(observed = written by NASA, inferred = derived from NASA notes, not_recorded = no outcome in the table)"
                        + (f"; oxygen {o2[0]:g}-{o2[-1]:g}%" if o2 else "; oxygen not recorded")
                        + (f"; lowest air flow {fl[0]:g}-{fl[-1]:g} cm/s" if fl else "")
                        + "; pressure assumed ISS/Cygnus cabin (~101 kPa, not in the NASA table). Source: gold/analytics/solid_fire_tests.csv.")
    drops = _rows(GOLD / "analytics" / "droplet_extinction_tests.csv")
    bd = defaultdict(list)
    for r in drops: bd[(r["fuel"], r["diluent"])].append(r)
    for (fuel, dil), rs in sorted(bd.items()):
        oc = Counter(r["outcome_class"] for r in rs)
        o2 = sorted(float(r["o2_pct"]) for r in rs if r["o2_pct"]); p = sorted(float(r["pressure_kpa"]) for r in rs if r["pressure_kpa"])
        out["PSI-69"].append(f"{len(rs)} FLEX {fuel} droplet tests with {dil} diluent: outcomes {dict(oc)}"
                             + (f"; oxygen {o2[0]:g}-{o2[-1]:g}%" if o2 else "") + (f"; pressure {p[0]:g}-{p[-1]:g} kPa (measured)" if p else "")
                             + ". Source: gold/analytics/droplet_extinction_tests.csv.")
    gas = _rows(GOLD / "analytics" / "gas_flame_tests.csv")
    ids = {"ACME CFI-G": "PSI-159", "ACME Flame Design": "PSI-10"}
    bg = defaultdict(list)
    for r in gas: bg[(r["investigation"], r["fuel"])].append(r)
    for (inv, fuel), rs in sorted(bg.items()):
        o2 = sorted(float(r["o2_pct"]) for r in rs if r["o2_pct"]); p = sorted(float(r["pressure_kpa"]) for r in rs if r["pressure_kpa"])
        oc = Counter(r["outcome_class"] for r in rs)
        out[ids[inv]].append(f"{len(rs)} {inv} gas-flame tests with {fuel}: outcomes {dict(oc)}"
                             + (f"; oxygen {o2[0]:g}-{o2[-1]:g}%" if o2 else "") + (f"; pressure {p[0]:g}-{p[-1]:g} kPa" if p else "")
                             + ". Gas flames, not cabin materials. Source: gold/analytics/gas_flame_tests.csv.")
    smoke = _rows(GOLD / "analytics" / "smoke_generation_tests.csv")
    bs = defaultdict(list)
    for r in smoke: bs[r["investigation"]].append(r)
    for inv, rs in bs.items():
        mats = Counter(r["material"] for r in rs)
        out["PSI-102" if inv == "SAME" else "PSI-101"].append(
            f"{len(rs)} {inv} smoke records from heated (not burning) materials: {dict(mats.most_common())}. "
            "Smoke particle data for detector design. Source: gold/analytics/smoke_generation_tests.csv.")
    return out


def _overview():
    """Cross-investigation facts computed from the Gold tables (oxygen / pressure ranges by fuel type, outcome basis)."""
    def rng(rows, col):
        v = sorted(float(r[col]) for r in rows if r.get(col))
        return (v[0], v[-1]) if v else None
    solids = _rows(GOLD / "analytics" / "solid_fire_tests.csv")
    drops = _rows(GOLD / "analytics" / "droplet_extinction_tests.csv")
    gas = _rows(GOLD / "analytics" / "gas_flame_tests.csv")
    out = []
    so, do, go = rng(solids, "o2_initial_pct"), rng(drops, "o2_pct"), rng(gas, "o2_pct")
    dp, gp = rng(drops, "pressure_kpa"), rng(gas, "pressure_kpa")
    basis = Counter(r["outcome_basis"] for r in solids)
    out.append(f"Oxygen ranges tested in microgravity across PSI: solid materials {so[0]:g}-{so[1]:g}% O2 ({len(solids)} tests, BASS, BASS-II, Saffire); "
               f"FLEX liquid droplets {do[0]:g}-{do[1]:g}% O2 ({len(drops)} tests); ACME gas flames {go[0]:g}-{go[1]:g}% O2 ({len(gas)} tests). "
               f"The highest oxygen tested in microgravity is {go[1]:g}% O2, in ACME gas flames (CFI-G), not with a solid material.")
    out.append(f"Pressure ranges across PSI: every solid-material space test is at assumed cabin pressure (~101 kPa, not in the NASA tables); "
               f"FLEX droplets {dp[0]:g}-{dp[1]:g} kPa (measured); ACME gas flames {gp[0]:g}-{gp[1]:g} kPa.")
    out.append(f"Outcome basis of the {len(solids)} solid-material space tests: {dict(basis)}. Only 'observed' outcomes were written by NASA.")
    out.append("All PSI flight combustion tests ran at about 0 g (ISS or the uncrewed Cygnus vehicle). PSI holds no partial-gravity "
               "(Moon 0.166 g or Mars 0.38 g) combustion tests.")
    return out


def build():
    profiles = json.loads((GOLD / "analytics" / "investigation_profiles.json").read_text(encoding="utf-8"))
    summaries = _table_summaries()
    docs, chunks = [], []

    offset = defaultdict(int)  # char offsets per (document, field): passages are consecutive pieces of that field

    def add_chunk(doc, field, content_type, text, i):
        k = (doc["document_id"], field); start = offset[k]; offset[k] += len(text) + 1
        chunks.append(dict(chunk_id=f"{doc['document_id']}#{field}-{i}", document_id=doc["document_id"], chunk_index=i,
                           char_start=start, char_end=start + len(text), page=None, title=doc["title"], year=doc["year"],
                           url=doc["url"], topic=doc["topic"], related_investigations=[doc["acronym"]] if doc.get("acronym") else [],
                           content_type=content_type, text=text, investigation_id=doc["investigation_id"], acronym=doc.get("acronym"),
                           field=field, source_path=doc["source_path"]))

    for p in profiles:
        acc = p["investigation_id"]
        src = PSI / INVESTIGATIONS[acc]["folder"] / "investigation.json"
        doc = dict(document_id=f"PSI-DOC-{acc}", ntrs_id=None, title=f"{p['acronym']} — {p['title']}", authors="NASA Physical Sciences Informatics",
                   year=(p.get("end_date") or "")[-4:] or None, sti_type="PSI_INVESTIGATION", url=p["psi_url"],
                   related_investigations=[p["acronym"]], bronze_path=rel(src), bronze_sha256=sha256(src),
                   investigation_id=acc, acronym=p["acronym"], kind="psi_investigation", topic=p["pillar"], source_path=rel(src))
        docs.append(doc)
        for field in ("objective", "hypothesis", "approach", "research_impacts"):
            for i, t in enumerate(_split(p.get(field) or "")):
                add_chunk(doc, field, "nasa_text", f"{p['acronym']} {field.replace('_', ' ')}: {t}", i)
        cond = "; ".join(
            f"{c['factor']} {c['min']:g}-{c['max']:g} {c['unit']}".strip() if c["kind"] == "range"
            else f"{c['factor']}: " + ", ".join(v["value"] for v in c["values"][:6]) for c in p["conditions"])
        meta = (f"{p['acronym']} ({acc}) is a {p['study_type']} investigation on {p['hardware'] or 'n/a'} [{p['hardware_family']}], fuel type {p['fuel_phase']}, "
                f"pillar {p['pillar']}{' + ' + p['pillar_secondary'] if p['pillar_secondary'] else ''}, relevance {p['relevance_tier']}. "
                f"{p['records']} records in its table. Conditions: {cond or 'none recorded'}. Varied between tests: {', '.join(p['varied_factors']) or 'none'}. "
                f"Not recorded: {', '.join(p['not_recorded_factors']) or 'none'}. Sensors named by NASA: {', '.join(s['sensor'] for s in p['sensors']) or 'none named'}. "
                f"Measured quantities named by NASA: {', '.join(m['sensor'] for m in p['measured_quantities']) or 'none named'}.")
        if p.get("partial_gravity_note"): meta += " " + p["partial_gravity_note"]
        for i, t in enumerate(_split(meta)): add_chunk(doc, "profile_summary", "computed_summary", t, i)
        for i, t in enumerate(summaries.get(acc, [])): add_chunk(doc, "table_summary", "computed_summary", f"{p['acronym']}: {t}", i)
        if p.get("data_files"):
            d = p["data_files"]
            add_chunk(doc, "data_files", "computed_summary",
                      f"{p['acronym']} data files in PSI: {d['files']} files, {d['total_gb']} GB; categories {d['categories']}; file types {d['file_types']}.", 0)
    odoc = dict(document_id="PSI-OVERVIEW", ntrs_id=None, title="Across all PSI combustion investigations (computed)", authors="AstroFire pipeline",
                year=None, sti_type="COMPUTED_OVERVIEW", url="https://psi.nasa.gov/physci/repo/search?q=combustion", related_investigations=[],
                bronze_path=None, bronze_sha256=None, investigation_id=None, acronym=None, kind="computed_overview", topic="overview",
                source_path="data/gold/analytics/*.csv")
    docs.append(odoc)
    for i, t in enumerate(_overview()):
        add_chunk(odoc, "overview", "computed_summary", t, i)
    cdoc = dict(document_id="CHALLENGE-RESOURCES", ntrs_id=None, title="Space Apps 2026 'Flame in Freefall' challenge resources",
                authors="NASA Space Apps Challenge", year="2026", sti_type="CHALLENGE_RESOURCE", url=CHALLENGE_URL, related_investigations=[],
                bronze_path=None, bronze_sha256=None, investigation_id=None, acronym=None, kind="challenge_resource",
                topic="challenge_resource", source_path="challenge resources tab")
    docs.append(cdoc)
    for i, (cid, title, url, text) in enumerate(CHALLENGE_RESOURCES):
        chunks.append(dict(chunk_id=f"CHALLENGE-RESOURCES#{cid}", document_id=cdoc["document_id"], chunk_index=i, char_start=0,
                           char_end=len(text), page=None, title=title, year="2026", url=url, topic="challenge_resource",
                           related_investigations=[], content_type="challenge_resource", text=text, investigation_id=None,
                           acronym=None, field=cid, source_path="challenge resources tab"))
    write_jsonl(GOLD / "rag" / "documents.jsonl", docs)
    write_jsonl(GOLD / "rag" / "chunks.jsonl", chunks)
    return docs, chunks


if __name__ == "__main__":
    d, c = build()
    print(f"documents {len(d)} | chunks {len(c)} | {Counter(x['content_type'] for x in c)}")
