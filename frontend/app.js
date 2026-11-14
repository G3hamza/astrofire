/* AstroFire Lite: backup UI. Same /api/* and the same honesty rules as the main app:
   verdicts shown verbatim, results never shown as odds, every test linked to NASA, missing values say "not available". */
"use strict";

const view = document.getElementById("view");
const banner = document.getElementById("banner");
const NA = '<i class="note">not available</i>';
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cache = new Map();

async function api(path, body) {
  const key = path + (body ? JSON.stringify(body) : "");
  if (!body && cache.has(key)) return cache.get(key);
  let res;
  try {
    res = await fetch(path, body ? { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) } : undefined);
  } catch {
    throw new Error("The AstroFire API is not reachable. Is the server running?");
  }
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  const data = await res.json();
  if (!body) cache.set(key, data);
  return data;
}

function showError(e) {
  banner.hidden = false;
  banner.textContent = e.message;
}

const outcomeClass = (o) => {
  const s = String(o || "").toLowerCase();
  if (s === "burned") return ["burned", "Burned"];
  if (s === "blowoff") return ["blowoff", "Blowoff"];
  if (["extinction", "went out", "no ignition", "not sustained"].includes(s)) return ["wentout", "Went out" + (s !== "went out" ? ` · ${o}` : "")];
  return ["unknown", "Not recorded"];
};
const tag = (o) => { const [c, t] = outcomeClass(o); return `<span class="tag ${c}">${esc(t)}</span>`; };
const basis = (b) => {
  const s = String(b || "").toLowerCase();
  const c = s.startsWith("observed") || s.startsWith("measured") ? "observed" : s.startsWith("inferred") ? "inferred" : s.startsWith("assumed") ? "assumed" : "unknown";
  const t = { observed: "Observed", inferred: "Inferred", assumed: "Assumed", unknown: "Not recorded" }[c];
  return `<span class="tag ${c}" title="${esc(b)}">${t}</span>`;
};
const link = (href, label) => href ? `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(label || href)}</a>` : NA;

/* ---------------- Home ---------------- */
async function home() {
  const [ov, st, ms, ex] = await Promise.all([api("/api/analytics/overview"), api("/api/stats"), api("/api/missions"),
    api("/api/scenario", { material: "PMMA (acrylic)", mission: "exploration" })]);
  const k = (n) => (ov.kpis.find((x) => x.kpi === n) || {}).value;
  const mars = ms.mars;
  const gas = (ex.atmosphere_evidence || []).find((a) => a.kind === "gas flame");
  view.innerHTML = `
    <section class="hero card">
      <div class="zero" style="color:var(--signal)">${esc(k("solid_flame_tests_total"))}</div>
      <div style="display:grid;gap:8px;flex:1;min-width:260px">
        <span class="eyebrow">solid-material fire tests in space</span>
        <h1>All at ${esc(k("o2_tested_min_pct"))}–${esc(k("o2_tested_max_pct"))}% oxygen and ~0 g. Habitats will run at ${esc(mars.o2_pct)}% oxygen, ${esc(mars.pressure_kpa)} kPa.</h1>
        <p class="note">No solid cabin material in NASA's PSI combustion data has been burned at that atmosphere or at Moon / Mars gravity.
          ${gas ? `Closest space flames: ACME gas flames at ${esc(gas.o2_pct)}% O₂ and ${esc(gas.pressure_kpa)} kPa (${link(gas.psi_url, "NASA PSI")}).` : ""}</p>
        <div class="btns"><a class="btn" href="#scenario">Check a scenario</a><a class="btn sec" href="#gaps">See the gaps</a></div>
      </div>
    </section>
    <section class="kpis">
      <div class="card kpi"><span class="eyebrow">Solid fire tests in space</span><b>${esc(k("solid_flame_tests_total") ?? "–")}</b></div>
      <div class="card kpi"><span class="eyebrow">Outcome written by NASA</span><b>${esc(k("pct_outcomes_observed") ?? "–")}%</b></div>
      <div class="card kpi"><span class="eyebrow">Oxygen in solid tests</span><b>${esc(k("o2_tested_min_pct"))}–${esc(k("o2_tested_max_pct"))}%</b></div>
      <div class="card kpi"><span class="eyebrow">Closest flame to habitat air</span><b>${gas ? `${esc(gas.o2_pct)}%` : "–"}</b><span class="note">${gas ? `${esc(gas.pressure_kpa)} kPa · ACME` : ""}</span></div>
      <div class="card kpi"><span class="eyebrow">Space flames in PSI</span><b>${esc(st.droplet_flame_tests + st.gas_flame_tests)}</b></div>
    </section>
    <section class="card"><h2>Solid-material space tests near each mission atmosphere</h2>
      <div class="scroll"><table><thead><tr><th>Mission</th><th>Atmosphere</th><th>Solid tests nearby</th><th></th></tr></thead><tbody>
      ${ov.mission_coverage.map((m) => `<tr><td>${esc(m.mission)}</td><td>${esc(m.o2_pct)}% O₂ · ${esc(m.pressure_kpa)} kPa · ${esc(m.gravity_g)} g</td>
        <td>${Number(m.space_solid_tests_near) ? esc(m.space_solid_tests_near) : `<span style="color:var(--burn)">${Number(m.gravity_g) > 0.01 ? "no space test at this gravity" : "no solid-material test at this atmosphere"}</span>`}</td>
        <td><a href="#scenario?mission=${esc(missionKey(m.mission))}">check →</a></td></tr>`).join("")}
      </tbody></table></div><p class="note">${esc(ov.mission_coverage[0]?.rule)}</p></section>`;
}
const missionKey = (n) => (n.startsWith("ISS") ? "iss" : n.startsWith("Explor") ? "exploration" : n.startsWith("Lunar") ? "moon" : "mars");

/* ---------------- Scenario ---------------- */
async function scenario(params) {
  const [fam, ms] = await Promise.all([api("/api/material-families"), api("/api/missions")]);
  const material = params.get("material") || "Aramid fabric (Nomex)";
  const mission = params.get("mission") || "iss";
  view.innerHTML = `
    <section class="card"><span class="eyebrow">Scenario check</span><h1>Will it burn here, and what proves it?</h1>
      <form id="sf" class="form">
        <label>Material<select id="mat">${fam.map((f) => `<option ${f.material === material ? "selected" : ""}>${esc(f.material)}</option>`).join("")}</select></label>
        <label>Mission<select id="mis">${Object.entries(ms).map(([k, m]) => `<option value="${k}" ${k === mission ? "selected" : ""}>${esc(m.name)}</option>`).join("")}</select></label>
        <label>Air flow (cm/s)<input id="flow" type="number" step="0.5" value="${esc(params.get("flow") || 5)}"></label>
        <button class="btn" type="submit">Check</button>
      </form></section>
    <div id="res" class="note">Loading…</div>`;
  document.getElementById("sf").addEventListener("submit", (e) => {
    e.preventDefault();
    location.hash = `scenario?material=${encodeURIComponent(document.getElementById("mat").value)}&mission=${document.getElementById("mis").value}&flow=${document.getElementById("flow").value}`;
  });
  const r = await api("/api/scenario", { material, mission, flow_cm_s: Number(params.get("flow") || 5) });
  const tone = r.verdict.startsWith("Insufficient") ? "danger" : r.verdict.includes("burns") ? "burn" : r.verdict.includes("goes out") ? "out" : "caution";
  const burned = r.evidence.filter((e) => outcomeClass(e.outcome)[0] === "burned").length;
  document.getElementById("res").outerHTML = `
    <section class="verdict v-${tone}"><span class="eyebrow">${tone === "danger" ? "NASA has no tests here" : "What NASA tests show"}</span>
      <b>${esc(r.verdict)}</b><span class="note">${esc(r.evidence_status)} · confidence: ${esc(r.confidence)}</span></section>
    <p class="note">Conditions: ${esc(r.scenario.o2_pct)}% O₂ · ${esc(r.scenario.pressure_kpa)} kPa · ${esc(r.scenario.gravity_g)} g · ${esc(r.scenario.flow_cm_s)} cm/s.
      Closest tests: <b>${burned} of ${r.evidence.length} burned</b> (a count of tests, not a probability).</p>
    ${r.blockers.length ? `<section class="card"><h2 style="color:var(--danger)">Why NASA can't answer this yet</h2><ul class="blockers">${r.blockers.map((b) => `<li>${esc(b)}</li>`).join("")}</ul></section>` : ""}
    ${(r.why_untested || []).length ? `<section class="card"><h2>Why NASA hasn't run this test in space</h2>${r.why_untested.map((w) => `<p>${esc(w.text)} ${link(w.source_url, "source")}</p>`).join("")}</section>` : ""}
    ${(r.atmosphere_evidence || []).length && (r.why_untested || []).some((w) => w.topic !== "gravity") ? `<section class="card"><h2>Closest space flames at this oxygen and pressure</h2><p class="note">Droplet (FLEX/CFI) and gas (ACME) flames on the ISS: not cabin materials, so they never change the verdict.</p><div class="scroll"><table><thead><tr><th>Test</th><th>Kind</th><th>Conditions</th><th>How it ended</th><th>Source</th></tr></thead><tbody>
      ${r.atmosphere_evidence.map((t) => `<tr><td class="mono">${esc(t.test_id)}</td><td>${esc(t.kind)} · ${esc(t.fuel)}</td><td>${esc(t.o2_pct)}% · ${esc(t.pressure_kpa)} kPa</td><td>${t.outcome_basis === "not_recorded" ? "not recorded" : t.test_end_raw === "SE" ? "self-extinguished" : t.test_end_raw === "FT" ? "burned until flow stopped" : esc(String(t.outcome).toLowerCase())}</td><td>${link(t.psi_url, "NASA PSI")}</td></tr>`).join("")}</tbody></table></div></section>` : ""}
    ${r.flags.length ? `<section class="card"><h2 style="color:var(--caution)">Notes on the evidence</h2><ul class="flags">${r.flags.map((f) => `<li>${esc(f)}</li>`).join("")}</ul></section>` : ""}
    <section class="card"><h2>${r.evidence.length} closest NASA space tests</h2><div class="scroll"><table>
      <thead><tr><th>Test</th><th>Material</th><th>O₂ %</th><th>Flow</th><th>Outcome</th><th>Basis</th><th>Pressure</th><th>Source</th></tr></thead><tbody>
      ${r.evidence.map((e) => `<tr><td class="mono">${esc(e.test_id)}<br><span class="note">${esc(e.investigation)}</span></td><td>${esc(e.material)}<br><span class="note">${e.same_material ? "same material" : esc(e.material_family)}</span></td>
        <td>${esc(e.o2_pct ?? "–")}</td><td>${esc(e.flow_cm_s ?? "–")}</td><td>${tag(e.outcome)}</td><td>${basis(e.outcome_basis)}</td><td>${basis(e.pressure_status)}</td>
        <td>${link(e.psi_url, "NASA PSI")}<br><span class="note mono" title="${esc(e.source_file)}">row ${esc(e.source_row)}</span></td></tr>`).join("")}
      </tbody></table></div></section>`;
}

/* ---------------- Gaps ---------------- */
async function gaps() {
  const cells = await api("/api/gaps");
  const o2 = [...new Set(cells.map((c) => c.o2_range))];
  const press = [...new Set(cells.map((c) => c.pressure))];
  const rows = [[1.0, "Earth 1 g"], [0.38, "Mars 0.38 g"], [0.166, "Moon 0.166 g"], [0.0, "Orbit ~0 g"]];
  const cell = (c) => {
    const pin = c.mission_design_points.map((m) => `<span class="pin">◆ ${esc(m.split(" ")[0])}</span>`).join("");
    if (c.gravity_g === 1.0) return `<div class="cell e">not in dataset${pin}</div>`;
    const fl = (c.gas_flame_tests || 0) + (c.droplet_tests || 0);
    if (c.space_tests) return `<div class="cell t"><b>${c.space_tests}</b>${fl ? `<span class="pin">+${fl} flames</span>` : ""}${pin}</div>`;
    if (fl) return `<div class="cell p">${fl} flames, no solids${pin}</div>`;
    return `<div class="cell n">no PSI test${pin}</div>`;
  };
  view.innerHTML = `<section class="card"><span class="eyebrow">Gaps map</span><h1>Where NASA has tested, and where it never has</h1>
    <p class="note">Each cell counts solid-material space fire tests in NASA's PSI tables. Dashed cells have droplet or gas flames (FLEX, CFI, ACME) but no solid material. ◆ = mission design point.
    PSI pressure for ISS/Cygnus tests is assumed ~101 kPa.</p></section>
    ${press.map((p) => `<section class="card"><h2>${esc(p)}</h2><div class="scroll"><div class="grid" style="min-width:560px">
      <div></div>${o2.map((b) => `<div class="note" style="text-align:center">${esc(b)} O₂</div>`).join("")}
      ${rows.map(([g, label]) => `<div class="note">${label}</div>${o2.map((b) => cell(cells.find((c) => c.gravity_g === g && c.o2_range === b && c.pressure === p))).join("")}`).join("")}
    </div></div></section>`).join("")}`;
}

/* ---------------- router ---------------- */
const ROUTES = { home, scenario, gaps };
async function route() {
  const [name, qs] = (location.hash.slice(1) || "home").split("?");
  const fn = ROUTES[name] || home;
  document.querySelectorAll("nav a").forEach((a) => a.classList.toggle("on", a.getAttribute("href") === `#${name || "home"}`));
  document.title = `${{ home: "Home", scenario: "Scenario", gaps: "Gaps" }[name] || "Home"} · AstroFire Lite`;
  banner.hidden = true;
  view.innerHTML = '<p class="note">Loading NASA data…</p>';
  try { await fn(new URLSearchParams(qs || "")); } catch (e) { showError(e); view.innerHTML = '<p class="note">Could not load this screen. Check that the server is running, then reload.</p>'; }
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);
route();
