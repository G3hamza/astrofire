"""Chat router + analyst: one entry point for the chatbot and POST /api/ask.

1. Understand: rule-first intent + entities (investigations, habitat, material, oxygen, pressure) from the message,
   with short conversation memory (last 6 turns) to resolve "it" / "that investigation" / the chosen habitat.
   If rules find no intent and an LLM is configured, the LLM classifies (router prompt).
2. Gather evidence with the tools for that intent (several tools for multi-part questions).
3. Draft a deterministic answer (template mode) - or let the LLM write it from the evidence only (analyst prompt).
4. Validate: citations must point to real evidence, no probabilities, numbers must be in evidence, insufficient-evidence
   verdicts are never overridden.
Returns the /api/ask contract: answer, findings[], interpretation[], limits[], followups[], tools_used[], mode, model
(+ intent, evidence[], sources[], suggested_followups[], insufficient_evidence, guardrails).
"""
from __future__ import annotations

import re
import time
import uuid

from . import features as F
from . import guardrails as G
from . import llm as L
from . import tools as T
from .config import llm_status
from .evidence import Registry
from .scenario_parse import extract
from .tables import by_acronym, habitats, profiles

MAX_Q, MAX_TURNS, MAX_TURN_CHARS = 1000, 6, 1500
INTENTS = ("ask", "scenario", "compare", "gaps", "summary", "rank", "datasets", "earth", "equipment", "out_of_scope")

# Investigation names as people write them -> id. Longest first so BASS-II wins over BASS, SAME-R over SAME.
_INV_PATTERNS = sorted([
    (r"\bBASS[- ]?II\b|\bBASS[- ]?2\b", "PSI-25"), (r"\bBASS\b(?![- ]?(II|2))", "PSI-26"),
    (r"\bSaffire[- ]?(III|3)\b", "PSI-100"), (r"\bSaffire[- ]?(II|2)\b", "PSI-99"), (r"\bSaffire[- ]?(I|1)\b(?![I\d])", "PSI-98"),
    (r"\bSAME[- ]?R\b", "PSI-101"), (r"\bSAME\b(?![- ]?R)", "PSI-102"), (r"\bFLEX[- ]?2\b", "PSI-68"), (r"\bFLEX\b(?![- ]?2)", "PSI-69"),
    (r"\bCFI[- ]?G\b", "PSI-159"), (r"\bCFI\b(?![- ]?G)", "PSI-39"), (r"\bE[- ]?FIELD\b", "PSI-22"), (r"\bBRE\b|burning rate emulator", "PSI-20"),
    (r"\bSPICE\b", "PSI-107"), (r"\bSLICE\b", "PSI-106"), (r"\bDAFT\b", "PSI-47"), (r"\bCLD\b", "PSI-21"), (r"\bs-?Flame\b", "PSI-23"),
    (r"flame design", "PSI-10"),
], key=lambda x: -len(x[0]))
_CASE_SENSITIVE = {"PSI-102", "PSI-101", "PSI-26", "PSI-25"}  # 'same' / 'bass' are also English words


def find_investigations(text: str) -> list[str]:
    found = []
    for pat, inv in _INV_PATTERNS:
        flags = 0 if inv in _CASE_SENSITIVE else re.I
        for m in re.finditer(pat, text or "", flags):
            found.append((m.start(), inv))
    out = []
    for _, inv in sorted(found):
        if inv not in out:
            out.append(inv)
    return out


def classify(msg: str, ent: dict, history_invs: list[str]) -> str:
    m = msg.lower()
    invs = ent["investigations"]
    if re.search(r"\b(make up|invent|fabricate|guess|estimate|predict)\b.*\b(value|number|rate|percent|temperature|limit|threshold)s?\b"
                 r"|\bgive me (a|an|the) (number|value|exact)", m):
        return "fabrication"
    if len(invs) >= 2 or (re.search(r"\b(compare|differ|difference|versus|vs\.?)\b", m) and len(invs + history_invs) >= 2):
        return "compare"
    if re.search(r"\b(would|will|does|do|can|could)\b.*\b(burn|ignite|catch fire|go out|extinguish|survive)\b|\bscenario\b|what happens to", m) \
            and (ent["material"] or ent["o2"] is not None or ent["habitat"]):
        return "scenario"
    if re.search(r"\b(gap|gaps|untested|(?:not|never) (?:been |yet )?tested|coverage|missing data|what hasn'?t)\b", m):
        return "gaps"
    if re.search(r"\b(dataset|datasets|train|training|machine learning|\bml\b|predictive|model the|modeling data|features)\b", m):
        return "datasets"
    if re.search(r"\bon earth\b|\bterrestrial\b|spinoff|firefighter|earth (application|benefit)", m):
        return "earth"
    if re.search(r"\b(detector|detection|extinguisher|suppression system|equipment|next[- ]generation|sensor design)\b", m):
        return "equipment"
    if re.search(r"\b(which|most relevant|matter|matters|rank|ranking|prioriti[sz]e|top|best)\b", m) and (ent["habitat"] or "habitat" in m or "base" in m):
        return "rank"
    if invs or (history_invs and re.search(r"\b(it|its|that|this|they|them|those)\b", m)):
        return "summary"
    return "ask"


def _llm_classify(msg: str) -> str | None:
    from .config import get_llm
    llm = get_llm()
    if llm is None:
        return None
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        out = L._text(llm.invoke([SystemMessage(L.prompt("router")), HumanMessage(msg[:MAX_Q])])).lower()
        return next((i for i in INTENTS if i in out), None)
    except Exception:
        return None


def _bounded(history: list | None) -> list[dict]:
    """Last 6 turns, text only, length-capped, roles user/assistant only (irrelevant/oversized history dropped)."""
    out = []
    for h in (history or [])[-MAX_TURNS:]:
        if isinstance(h, dict) and h.get("role") in ("user", "assistant") and isinstance(h.get("content"), str):
            out.append({"role": h["role"], "content": G.redact_secrets(h["content"][:MAX_TURN_CHARS])})
    return out


def _entities(msg: str, history: list[dict], habitat: str | None) -> dict:
    ent = extract(msg)
    ent["investigations"] = find_investigations(msg)
    hist_text = " ".join(h["content"] for h in history)
    hist_invs = find_investigations(hist_text)
    if not ent["habitat"]:
        ent["habitat"] = habitat if habitat in habitats() else None
    if not ent["habitat"]:
        for h in reversed(history):
            hh = extract(h["content"])["habitat"]
            if hh:
                ent["habitat"], ent["habitat_from"] = hh, "conversation"
                break
    ent["history_investigations"] = hist_invs
    return ent


# ---------------------------------------------------------------------------------------------------------------
def _followups(intent: str, ent: dict, reg: Registry) -> list[str]:
    """Context-built suggestions (not a fixed list): based on what this answer covered and what it lacks."""
    hab = habitats().get(ent.get("habitat") or "moon")
    invs = [profiles()[i]["acronym"] for i in ent["investigations"]] or [e.acronym for e in reg.items if e.acronym][:2]
    first = invs[0] if invs else "BASS-II"
    other = next((a for a in ("BASS-II", "FLEX", "SAME-R", "ACME CFI-G", "SAFFIRE-II") if a not in invs), "FLEX")
    pool = {
        "scenario": [f"Which investigations matter most for a {hab['name'].lower()}?", f"What gaps exist for solid materials at {hab['o2_pct']:g}% oxygen?",
                     f"Summarize what {first} tested."],
        "rank": [f"Summarize what {first} found.", f"How do {first} and {other} differ?", f"What has never been tested for a {hab['name'].lower()}?"],
        "compare": [f"Summarize {first} in detail.", f"Which of these matters most for a {hab['name'].lower()}?", "What data could I use to train a flammability model?"],
        "gaps": [f"Would Nomex burn at {hab['o2_pct']:g}% oxygen in a {hab['name'].lower()}?", "Which investigations come closest to the habitat atmosphere?",
                 "What does E-FIELD Flames tell us about partial gravity?"],
        "summary": [f"How do {first} and {other} differ?", f"Which investigations matter most for a {hab['name'].lower()}?", f"What did {first} not record?"],
        "datasets": ["Which outcomes in BASS-II were written by NASA versus inferred?", "What conditions did FLEX vary?", "What gaps limit a Moon-base model?"],
        "earth": ["What does SAME-R mean for smoke detectors?", "How did FLEX test fire suppressants?", "Which investigations matter most for the ISS?"],
        "equipment": ["How do SAME and SAME-R differ?", "What smoke particle data exists for Kapton?", "Which suppression research is closest to a Moon base?"],
    }
    return pool.get(intent, [f"Which investigations matter most for a {hab['name'].lower()}?", f"Summarize what {first} found.",
                             "What has never been tested for a Moon base?"])[:3]


def _gather(intent: str, msg: str, ent: dict, reg: Registry) -> dict:
    """Run the tools for an intent. Returns context for the template answer."""
    ctx: dict = {"limits": [], "insufficient": False}
    hab_key = ent.get("habitat") or "moon"
    invs = ent["investigations"] or (ent["history_investigations"][-1:] if intent in ("summary", "compare") else [])
    try:
        if intent == "scenario":
            hab = habitats()[ent["habitat"] or "iss"]
            s = F.scenario(ent["habitat"] or "iss", ent["o2"], ent["pressure"], ent["material"], gravity_g=ent["gravity"])
            sreg = s.pop("_registry")
            reg.items, reg.tools_used = sreg.items, sreg.tools_used
            ctx.update(scenario=s, insufficient=s["verdict"].startswith("Insufficient"))
            if not ent["habitat"] and ent["gravity"] is None:
                ctx["limits"].append(f"No environment named; the {hab['name']} preset was used ({hab['gravity_g']:g} g, {hab['o2_pct']:g}% O2, {hab['pressure_kpa']:g} kPa).")
            ctx["limits"] += s["caveats"]
        elif intent == "rank":
            pillar = "detection" if "smoke" in msg.lower() or "detect" in msg.lower() else "suppression" if "suppress" in msg.lower() else None
            ctx["rank"] = T.rank_habitat(reg, hab_key, pillar, top=5)
        elif intent == "compare":
            ids = invs if len(invs) >= 2 else (ent["history_investigations"][-2:] + invs)[-3:]
            c = F.compare(ids[:3] if len(ids) >= 2 else ids + ["PSI-25"])
            creg = c.pop("_registry")
            reg.items, reg.tools_used = creg.items, creg.tools_used
            ctx["compare"] = c
        elif intent == "gaps":
            g = F.gaps()
            greg = g.pop("_registry")
            reg.items, reg.tools_used = greg.items, greg.tools_used
            ctx["gaps"] = g
        elif intent == "summary":
            inv = invs[0]
            ctx["profile"] = T.get_investigation(reg, inv, ("objective", "research_impacts"))
            p = profiles()[inv]
            kind = {"solid": "solid", "liquid droplet": "droplet", "smoke (heated materials)": "smoke", "gas": "gas"}.get(p["fuel_phase"])
            if kind and (kind != "gas" or inv in ("PSI-159", "PSI-10")) and (kind != "droplet" or inv == "PSI-69"):
                ctx["records"] = T.search_records(reg, kind, investigation=inv, material=ent["material_word"], limit=4)
            T.search_passages(reg, msg, k=2, investigation=inv)
        elif intent == "datasets":
            ctx["datasets"] = T.list_datasets(reg)
            ctx["limits"].append("The ML table is not validated; AstroFire does not present any model output as a prediction.")
        elif intent == "earth":
            T.search_passages(reg, "Earth application spinoff firefighter detector extinguisher", k=4, content_type="challenge_resource")
            T.search_passages(reg, "Earth benefits terrestrial fire safety " + msg, k=3, content_type="nasa_text")
            ctx["limits"].append("These are connections NASA or the challenge describe; PSI data does not validate Earth products directly.")
        elif intent == "equipment":
            pillar = "suppression" if re.search(r"suppress|extingu", msg, re.I) else "detection"
            ctx["rank"] = T.rank_habitat(reg, hab_key, pillar, top=4)
            T.search_passages(reg, f"{pillar} research impacts future spacecraft " + msg, k=4, content_type="nasa_text")
        else:
            T.search_passages(reg, msg, k=6, investigation=invs[0] if invs else None)
    except T.ToolError as e:
        ctx["limits"].append(str(e))
        ctx["tool_error"] = str(e)
    return ctx


def _template(intent: str, msg: str, ent: dict, reg: Registry, ctx: dict) -> dict:
    """Deterministic answer from evidence (template mode, also the fallback when the LLM fails a guardrail)."""
    ids = [e.id for e in reg.items]
    direct = [e for e in reg.items if e.level == "direct"][:5]
    findings, interp, limits = [], [], list(ctx["limits"])
    if "tool_error" in ctx and not reg.items:
        return {"answer": f"{G.INSUFFICIENT} {ctx['tool_error']}", "findings": [], "interpretation": [], "limits": limits}
    if intent == "scenario":
        s = ctx["scenario"]
        answer = f"Verdict from AstroFire's rule engine: {s['verdict']} (coverage: {s['coverage']})."
        if s["verdict"].startswith("Insufficient"):
            answer = f"{G.INSUFFICIENT} " + answer
        findings = list(s["reasons"])
        b = next((e for e in reg.items if e.kind == "bound" and e.text.startswith("Do the bounds")), None)
        if b:
            findings.append(f"{b.text} [{b.id}]")
        limits += s["blockers"][1:]
        interp.append("Closest tests are analogues, not proof: they differ from the requested conditions as listed above.")
    elif intent == "rank":
        r = ctx["rank"]
        top = ", ".join(f"{x['acronym']} ({x['score']:.0f})" for x in r["ranked"][:3])
        answer = f"For the {r['habitat']['name']}, the most relevant PSI investigations are {top} [{r['evidence'][0]}]."
        findings = [f"{reg.get(i).text} [{i}]" for i in r["evidence"]]
        interp.append("AstroFire interpretation: the ranking weighs condition closeness, challenge relevance, fuel type and evidence quality; it is a relevance order, not a safety rating.")
        if r["habitat"]["gravity_g"] > 0:
            limits.append("PSI has no partial-gravity combustion data; every investigation only bounds this gravity from ~0 g.")
    elif intent == "compare":
        c = ctx["compare"]
        answer = c["narrative"]
        findings = [f"{t['attribute']}: " + "; ".join(f"{k} = {v}" for k, v in t["values"].items()) + (" (differs)" if t["differs"] else " (same)")
                    + f" [{ids[-1]}]" for t in c["table"]]
        findings = [f for f in findings if "(differs)" in f][:6] + [f for f in findings if "(same)" in f][:3]
        findings += [f"{e.text[:300]} [{e.id}]" for e in reg.items if e.kind == "investigation" and e.level == "direct"]
    elif intent == "gaps":
        g = ctx["gaps"]
        answer = g["narrative"]
        findings = [f"{e.text} [{e.id}]" for e in reg.items if e.kind == "gap"][:5]
        interp.append("AstroFire interpretation: microgravity results can only bound Moon/Mars behavior; partial-gravity tests (LUCI, FM2) are needed to close this gap.")
    elif intent == "datasets":
        answer = "These Gold datasets hold NASA test conditions and outcomes you can use for modeling; each lists its real columns and limits."
        findings = [f"{reg.get(i).text} [{i}]" for i in ctx["datasets"]]
    elif intent == "fabrication":
        answer = f"{G.INSUFFICIENT} AstroFire does not invent measurements, thresholds or predictions; it reports only values in NASA's PSI records."
    else:
        if not reg.items:
            return {"answer": G.OFF_TOPIC, "findings": [], "interpretation": [], "limits": limits}
        # general questions: keep retrieval rank (best match first); other intents: NASA's own text first
        order = list(reg.items) if intent == "ask" else direct + [e for e in reg.items if e not in direct]
        if intent == "earth":   # lead with the Earth applications the challenge lists, then NASA's own impact text
            order = [e for e in reg.items if e.kind == "resource"] + [e for e in reg.items if e.kind != "resource"]
        if intent == "summary" and re.search(r"vary|varied|condition|sensor|measure|record|hardware", msg, re.I):
            order = [e for e in reg.items if e.level == "analysis" and e.kind == "investigation"] + [e for e in order if not (e.level == "analysis" and e.kind == "investigation")]
        lead = order[0]
        answer = f"{lead.text[:900 if lead.level == 'analysis' else 450]} [{lead.id}]"
        findings = [f"{e.text[:350]} [{e.id}]" for e in order[1:6]]
        if intent in ("earth", "equipment"):
            interp.append("AstroFire interpretation: these are design implications suggested by the NASA research aims above, not tested product results.")
        if intent == "summary" and ctx.get("records"):
            rec = ctx["records"]
            if rec["summary"]:
                findings.insert(0, f"{reg.get(rec['summary']).text} [{rec['summary']}]")
            if rec["basis"].get("inferred"):
                limits.append("Many outcomes in this table are inferred from NASA notes, not written by NASA.")
    return {"answer": answer, "findings": findings, "interpretation": interp, "limits": limits}


def analyze(question: str, habitat: str | None = None, history: list | None = None) -> dict:
    t0 = time.time()
    rid = uuid.uuid4().hex[:12]
    q = (question or "").strip()
    status = llm_status()
    base = {"request_id": rid, "tools_used": [], "evidence": [], "sources": [], "findings": [], "interpretation": [], "limits": [],
            "insufficient_evidence": False, "guardrails": [], "model": status["model"]}
    if not q:
        return {**base, "intent": "out_of_scope", "answer": "Please ask a question about NASA PSI combustion research.", "followups": [],
                "suggested_followups": [], "mode": "template", "latency_ms": 0}
    if len(q) > MAX_Q:
        q = q[:MAX_Q]
        base["limits"].append(f"Question truncated to {MAX_Q} characters.")
    hist = _bounded(history)
    injection = G.looks_like_injection(q)
    ent = _entities(G.sanitize(q) if injection else q, hist, habitat)
    if injection:
        base["guardrails"].append("prompt_injection_ignored")
        base["limits"].append("Instructions inside the question that try to change AstroFire's rules or reveal configuration were ignored.")
    clean_q = G.sanitize(q) or q
    if G.is_off_topic(clean_q, history_has_context=bool(ent["history_investigations"])) or (injection and not G.DOMAIN.search(clean_q)):
        fu = _followups("ask", ent, Registry())
        return {**base, "intent": "out_of_scope", "answer": G.OFF_TOPIC, "followups": fu, "suggested_followups": fu, "mode": "template",
                "limits": base["limits"] + ["AstroFire answers questions about NASA PSI combustion and spacecraft / habitat fire safety. "
                                            "Rocket and propellant fires are outside the PSI data."],
                "latency_ms": int((time.time() - t0) * 1000)}
    intent = classify(clean_q, ent, ent["history_investigations"])
    if intent == "ask" and not ent["investigations"]:
        intent = _llm_classify(clean_q) or "ask"
        if intent in ("summary", "compare") and not (ent["investigations"] or ent["history_investigations"]):
            intent = "ask"
        if intent == "out_of_scope":
            intent = "ask"   # rules found domain words: answer from evidence rather than refusing
    reg = Registry()
    tok = L.SKIP_LLM.set(True)
    try:
        ctx = _gather(intent, clean_q, ent, reg)
    finally:
        L.SKIP_LLM.reset(tok)
    draft = _template(intent, clean_q, ent, reg, ctx)
    mode, events = "template", []
    if status["ai_enabled"] and reg.items and intent != "fabrication":
        extra = ""
        if ctx.get("scenario"):
            extra = (f"VERDICT (fixed, from the rule engine): {ctx['scenario']['verdict']}. Coverage: {ctx['scenario']['coverage']}. "
                     "Explain what the closest solid-material test and the closest flames at this oxygen and pressure (e.g. FLEX droplets) "
                     "show, and how each differs from the request (gravity, oxygen, pressure, fuel type).")
        if ctx.get("compare"):
            extra = "COMPARISON TABLE:\n" + "\n".join(f"{t['attribute']}: {t['values']} differs={t['differs']}" for t in ctx["compare"]["table"])
        text, events = L.write("analyst", clean_q, reg.block(), extra, history=hist)
        if text:
            sec = L.sections(text)
            valid = {e.id for e in reg.items}
            fnd = [L.keep_valid_citations(f, valid) for f in sec["findings"]]
            dropped = [f for f in fnd if not L.cited_ids(f)]
            fnd = [f for f in fnd if L.cited_ids(f)]
            if sec["answer"] and (fnd or not draft["findings"]):
                mode = "ai"
                if intent == "scenario":  # closest-evidence reasons are deterministic facts: always kept, AI findings added after
                    fnd = draft["findings"] + [f for f in fnd if f not in draft["findings"]][:2]
                draft = {"answer": L.keep_valid_citations(sec["answer"], valid), "findings": fnd,
                         "interpretation": [L.keep_valid_citations(x, valid) for x in sec["interpretation"]],
                         "limits": list(dict.fromkeys(draft["limits"] + sec["limits"]))}
                if dropped:
                    draft["limits"].append(f"{len(dropped)} statement(s) were removed because their citation could not be verified.")
                if len(sec["followups"]) >= 3:
                    ctx["followups"] = [G.strip_probability(x) for x in sec["followups"][:3]]
            else:
                events.append("ai_answer_rejected_no_valid_citations")
    if ctx.get("scenario") and ctx["scenario"]["verdict"] not in draft["answer"]:   # the engine's verdict is always stated
        draft["answer"] = f"Verdict from AstroFire's rule engine: {ctx['scenario']['verdict']}. " + draft["answer"]
    insufficient = ctx.get("insufficient") or intent == "fabrication" or draft["answer"].startswith(G.INSUFFICIENT)
    if insufficient and not draft["answer"].startswith(G.INSUFFICIENT):
        draft["answer"] = f"{G.INSUFFICIENT} {draft['answer']}"
    for k in ("answer",):
        draft[k] = G.strip_probability(G.redact_secrets(draft[k])) or draft[k]
    for k in ("findings", "interpretation", "limits"):
        draft[k] = [G.redact_secrets(x) for x in draft[k] if x and not G.no_probability_violations(x)]
    cited = set(L.cited_ids(" ".join([draft["answer"]] + draft["findings"] + draft["interpretation"])))
    evidence = [e.public() for e in reg.items if e.id in cited] or [e.public() for e in reg.items][:8]
    fu = ctx.get("followups") or _followups(intent, ent, reg)
    shown = " ".join(draft["findings"])
    limits = [x for x in dict.fromkeys(base["limits"] + draft["limits"]) if x not in shown]
    return {**base, "intent": intent, **draft, "limits": limits,
            "followups": fu, "suggested_followups": fu, "tools_used": reg.tools_used, "evidence": evidence,
            "sources": reg.sources([e["id"] for e in evidence]), "insufficient_evidence": bool(insufficient),
            "guardrails": base["guardrails"] + events, "mode": mode, "model": (next((g.split(":", 1)[1] for g in events if g.startswith("served_by:")), status["model"]) if mode == "ai" else None),
            "entities": {k: ent[k] for k in ("habitat", "material", "o2", "pressure", "gravity", "investigations")},
            "latency_ms": int((time.time() - t0) * 1000)}


def chat(message: str, history: list | None = None, habitat: str | None = None) -> dict:
    """Teammate contract: {intent, answer, evidence[], sources[], suggested_followups[3]} (+ the analyst fields)."""
    return analyze(message, habitat, history)
