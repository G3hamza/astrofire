import { Database, Droplets, Flame, Wind } from "lucide-react";
import { useMemo, useState } from "react";
import { CartesianGrid, ReferenceDot, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import { SourceChip } from "../components/SourceChip";
import { ChallengeResources } from "../components/WhyItMatters";
import { Card, CardHeader, cx, ErrorState, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client, PSI_PORTAL } from "../lib/client";
import type { CsvRow } from "../lib/types";

import { heroTitle, PageHero } from "../components/PageHero";
/* Every NASA investigation in the dataset, what it measured, and how StarryNight uses it.
   Droplets, smoke and gas jets are different experiment kinds and are never mixed into solid-material results. */

const ROLE: Record<string, { what: string; use: string; where?: string; Icon: typeof Flame }> = {
  "BASS-II": { what: "Solid samples (PMMA, Nomex, cotton-fiberglass...) burning or going out in low-speed air flow; O₂ lowered below 21% with nitrogen.", use: "Core evidence for Scenario, Gaps, flammability map, Materials.", where: "/scenario", Icon: Flame },
  BASS: { what: "Earlier solid-sample burns in the same glovebox; many outcomes not recorded.", use: "Solid-material evidence where conditions were recorded.", where: "/materials", Icon: Flame },
  "SAFFIRE-I": { what: "Large cotton-fiberglass fire in the uncrewed Cygnus after it left the ISS.", use: "Large-scale solid evidence in Scenario and Gaps.", where: "/gaps", Icon: Flame },
  "SAFFIRE-II": { what: "Nine samples ignited in Cygnus (material flammability limits at large scale).", use: "Solid-material evidence.", where: "/gaps", Icon: Flame },
  "SAFFIRE-III": { what: "Repeat of large-scale Cygnus fire; outcome not in the PSI table.", use: "Listed; outcome not recorded.", where: "/data", Icon: Flame },
  FLEX: { what: "Fuel droplets (methanol, heptane) burned on the ISS at 12–34% O₂ and 70–309 kPa, with nitrogen, CO₂ or helium.", use: "Atmosphere evidence: what flames did at a given oxygen and pressure (shown apart from materials).", where: "#flex", Icon: Droplets },
  CFI: { what: "Cool Flames Investigation: 79 unique droplet tests (dodecane and blends) at 0.5–5 atm with 17% or 21% O₂, some in helium. NASA's table gives the conditions but no outcome.", use: "Atmosphere evidence at low pressure (down to 50.7 kPa), labelled 'outcome not recorded'; droplet counts on Gaps.", where: "#flex", Icon: Droplets },
  "FLEX-2": { what: "Test matrix only: for each of 8 fuels, the range of conditions run (O₂ 17–30%, 0.5–3 atm, flow 0.1–5 cm/s). No per-test rows or outcomes.", use: "Shown as a test matrix; never counted as tests.", where: "#flex2", Icon: Droplets },
  SAME: { what: "Smoke particles from overheated (not burning) Teflon, Kapton, silicone, lampwick, DBP.", use: "Smoke conditions per material (detection, not flammability).", where: "#smoke", Icon: Wind },
  "SAME-R": { what: "Reflight of SAME with 109 runs at different flows, heater levels and aging times.", use: "Smoke conditions per material.", where: "#smoke", Icon: Wind },
  SPICE: { what: "Gas-jet flames (propylene, ethylene, propane...) and the smoke point where they start to emit soot.", use: "Flame/soot context (not material flammability).", where: "#spice", Icon: Flame },
  "BASS-Modeling": { what: "Computer model of BASS flames. NASA PSI holds only a 9.47 KB metadata file: no data table.", use: "Listed for completeness; no data to load.", Icon: Database },
  "ACME CFI-G": { what: "333 gas-jet flame tests (ethane, propane, butane) at 12–85% O₂ and 0.5–3.3 bar. NASA recorded how each flame ended: SE self-extinguished, FT flow terminated while burning.", use: "Atmosphere evidence: includes flames at 34.1% O₂ and 50.7 kPa, next to the habitat point. 861 blank rows in NASA's file skipped.", where: "#acme", Icon: Flame },
  "ACME Flame Design": { what: "327 ethylene/propane flame tests at 19.8–85% O₂ and 43–306 kPa (measured). No outcome column.", use: "Atmosphere evidence, labelled 'outcome not recorded'.", where: "#acme", Icon: Flame },
  "ACME BRE": { what: "Burning Rate Emulator: a gas burner built to imitate a burning solid. 18 test days, flames ignited at 21, 25, 26.5, 34 and 40% O₂; pressure varied but not recorded.", use: "Session log (not individual tests). Two typos fixed: '3400%' read as 34, '2100%' as 21.", where: "#logs", Icon: Flame },
  "ACME CLD": { what: "Coflow laminar diffusion flames: 32 test days with fuel concentrations and flames ignited.", use: "Session log, not tests.", where: "#logs", Icon: Flame },
  "ACME E-FIELD": { what: "Flames in an electric field: 32 test days with mesh polarity and flames ignited.", use: "Session log, not tests.", where: "#logs", Icon: Flame },
  "ACME s-Flame": { what: "Spherical flames: 18 test days at ~21% O₂ and ~1 atm (nitrogen or helium).", use: "Session log, not tests. 'N3/N4' typos read as N2.", where: "#logs", Icon: Flame },
  SLICE: { what: "Structure and Liftoff in Combustion: 12 test days of gas-jet flames (methane, ethylene, ethane).", use: "Session log, not tests.", where: "#logs", Icon: Flame },
  "Cool-flame counterflow study": { what: "Ground analysis of FLEX data: the PSI table is a list of 8 figures in its journal paper.", use: "Figure index; listed, no test data.", where: "#logs", Icon: Database },
  DAFT: { what: "Dust and Aerosol Feasibility Test: 2 sampling sessions with Arizona road dust, to check SAME's particle counters.", use: "Sampling log, not fire tests.", where: "#logs", Icon: Wind },
  "SPICE analysis": { what: "Analysis project on SPICE data. No data table in PSI.", use: "Listed for completeness.", Icon: Database },
  "SAME data study": { what: "Study using SAME smoke data. No data table in PSI.", use: "Listed for completeness.", Icon: Database },
  "Cool-flame CFD": { what: "CFD model of FLEX cool flames. No data table in PSI.", use: "Listed for completeness.", Icon: Database },
};

export default function ExperimentsPage() {
  const inv = useQuery("investigations", client.investigations);
  return (
    <div className="space-y-8">
      <PageHero photo="saffire" variant="band">
        <p className="kicker">NASA experiments</p>
        <h1 className={heroTitle}>Every investigation, and what it can tell us</h1>
        <p className="max-w-3xl text-lg text-muted">
          All 24 combustion investigations in NASA's PSI repository are loaded, cleaned and validated. Solid-material burns answer
          "will it burn". Droplets, gas flames and smoke measure other things, so they get their own place and are never counted as material tests.
        </p>
      </PageHero>

      {inv.error ? <ErrorState message={inv.error} onRetry={inv.reload} /> : !inv.data ? <Skeleton className="h-64 rounded-card" /> : (
        <div className="grid gap-3 md:grid-cols-2">
          {inv.data.map((i) => {
            const r = ROLE[i.acronym];
            const Icon = r?.Icon ?? Database;
            return (
              <Card key={i.investigation_id} className="flex flex-col gap-2 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <Icon size={16} className="text-signal" aria-hidden />
                  <h2 className="text-h3">{i.acronym}</h2>
                  <span className="text-sm text-faint">{i.platform}</span>
                  <span className="tnum ml-auto text-sm text-muted">{Number(i.records)} rows</span>
                </div>
                <p className="text-sm text-ink/90">{r?.what ?? i.title}</p>
                <p className="text-sm text-muted"><b className="text-ink">In StarryNight:</b> {r?.use ?? "Loaded in the pipeline."}</p>
                <div className="mt-auto flex flex-wrap items-center gap-2 pt-1">
                  <SourceChip href={`${PSI_PORTAL}/${i.investigation_id}`} label={`NASA PSI · ${i.investigation_id}`} />
                  {r?.where && <a href={r.where} className="text-sm">See it →</a>}
                </div>
              </Card>
            );
          })}
        </div>
      )}

      <FlexSection />
      <GasSection />
      <Flex2Section />
      <LogsSection />
      <SmokeSection />
      <SpiceSection />
      <ChallengeResources />
    </div>
  );
}

/* ---------------- FLEX ---------------- */
const END_COLOR: Record<string, string> = { Extinction: "rgb(var(--out))", Burned: "rgb(var(--burn))", Disruption: "rgb(var(--blow))" };
const END_LABEL: Record<string, string> = { Extinction: "extinction", Burned: "completion", Disruption: "disruption" };
const DILUENTS = ["N2 (air-like)", "CO2", "He"];

function FlexSection() {
  const q = useQuery("droplets", client.droplets);
  const cfi = useQuery("cool-flames", client.coolFlames);
  const ms = useQuery("missions", client.missions);
  const [dil, setDil] = useState("N2 (air-like)");
  const pts = useMemo(() => (q.data ?? [])
    .filter((r) => r.diluent === dil && r.o2_pct && r.pressure_kpa)
    .map((r) => ({ x: Number(r.pressure_kpa), y: Number(r.o2_pct), end: r.outcome_class, r })), [q.data, dil]);
  const cfiPts = useMemo(() => (cfi.data ?? [])
    .filter((r) => (dil === "He" ? r.diluent === "He" : dil === "N2 (air-like)" ? r.diluent.startsWith("N2") : false) && r.o2_pct && r.pressure_kpa)
    .map((r) => ({ x: Number(r.pressure_kpa), y: Number(r.o2_pct), end: "CFI", r: { ...r, outcome_class: "not recorded" } })), [cfi.data, dil]);
  const ends = ["Extinction", "Disruption", "Burned"];
  const hab = ms.data?.mars; const iss = ms.data?.iss;
  const near = (q.data ?? []).filter((r) => r.diluent.startsWith("N2") && Number(r.o2_pct) >= 30 && Number(r.pressure_kpa) < 80);

  return (
    <Card id="flex">
      <CardHeader eyebrow="FLEX · fuel droplets on the ISS" title="Oxygen and pressure NASA flames have actually seen in orbit"
        right={<div className="flex gap-1" role="radiogroup" aria-label="Diluent gas">
          {DILUENTS.map((d) => (
            <button key={d} role="radio" aria-checked={dil === d} onClick={() => setDil(d)}
              className={cx("rounded-md border px-2 py-1 text-[12px]", dil === d ? "border-signal bg-signal/15 text-signal" : "border-line text-muted")}>{d}</button>
          ))}
        </div>} />
      <div className="space-y-3 p-5">
        {q.error ? <ErrorState message={q.error} onRetry={q.reload} /> : !q.data ? <Skeleton className="h-80" /> : (
          <>
            <ul className="flex flex-wrap gap-4 text-sm" aria-label="Legend">
              {ends.map((e) => <li key={e} className="flex items-center gap-2"><span className="h-3 w-3 rounded-full" style={{ background: END_COLOR[e] }} />FLEX: ended by {END_LABEL[e]}</li>)}
              <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full border-2" style={{ borderColor: "rgb(var(--muted))" }} />CFI: outcome not recorded</li>
              <li className="flex items-center gap-2"><span className="h-3 w-3 rotate-45 border-2" style={{ borderColor: "rgb(var(--danger))" }} />Moon/Mars habitat point</li>
            </ul>
            <div className="h-80" role="img" aria-label={`FLEX droplet tests with ${dil}: pressure versus oxygen`}>
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 24, left: 4 }}>
                  <CartesianGrid stroke="rgb(var(--line) / 0.5)" vertical={false} />
                  <XAxis type="number" dataKey="x" domain={[40, 320]} tick={{ fill: "rgb(var(--faint))", fontSize: 12 }} stroke="rgb(var(--line))"
                    label={{ value: "Pressure (kPa, measured)", fill: "rgb(var(--faint))", fontSize: 12, position: "bottom", offset: 8 }} />
                  <YAxis type="number" dataKey="y" domain={[10, 40]} tick={{ fill: "rgb(var(--faint))", fontSize: 12 }} stroke="rgb(var(--line))" width={44}
                    label={{ value: "Oxygen %", fill: "rgb(var(--faint))", fontSize: 12, angle: -90, position: "insideLeft", offset: 12 }} />
                  <Tooltip content={<FlexTip />} />
                  <Scatter data={cfiPts} fill="rgb(var(--surface))" stroke="rgb(var(--muted))" strokeWidth={1.5} isAnimationActive={false} />
                  {ends.map((e) => <Scatter key={e} data={pts.filter((p) => p.end === e)} fill={END_COLOR[e]} isAnimationActive={false} />)}
                  {hab && <ReferenceDot x={hab.pressure_kpa} y={hab.o2_pct} r={8} fill="none" stroke="rgb(var(--danger))" strokeWidth={2}
                    label={{ value: "habitat", fill: "rgb(var(--danger))", fontSize: 12, position: "left" }} />}
                  {iss && <ReferenceDot x={iss.pressure_kpa} y={iss.o2_pct} r={6} fill="none" stroke="rgb(var(--muted))" strokeWidth={2}
                    label={{ value: "ISS air", fill: "rgb(var(--muted))", fontSize: 12, position: "top" }} />}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-muted">
              <b className="tnum text-ink">{near.length}</b> nitrogen-diluted FLEX tests ran at 30% O₂ or more below 80 kPa, the closest any space flame has come
              to the habitat point. CFI adds <b className="tnum text-ink">{(cfi.data ?? []).filter((r) => Number(r.pressure_kpa) < 80).length}</b> tests below 80 kPa, but only at 21% O₂ and without recorded outcomes.
              These are liquid fuel droplets, not cabin materials, so StarryNight shows them as atmosphere evidence only.
            </p>
            <div className="flex flex-wrap gap-2">
              <SourceChip href={`${PSI_PORTAL}/PSI-69`} label="NASA PSI · FLEX (PSI-69)" />
              <SourceChip href={`${PSI_PORTAL}/PSI-39`} label="NASA PSI · CFI (PSI-39)" />
            </div>
          </>
        )}
      </div>
    </Card>
  );
}

function FlexTip({ active, payload }: { active?: boolean; payload?: { payload: { r: CsvRow } }[] }) {
  if (!active || !payload?.length) return null;
  const r = payload[0].payload.r;
  return (
    <div className="rounded-lg border border-line bg-surface p-3 text-sm shadow-card">
      <p className="font-mono text-ink">{r.test_id} · {r.fuel}</p>
      <p className="tnum text-muted">{r.o2_pct}% O₂ · {r.pressure_kpa} kPa · {r.diluent}</p>
      <p className="text-muted">test ended by {END_LABEL[r.outcome_class] ?? r.outcome_class}{r.burn_time_s ? ` after ${r.burn_time_s} s` : ""}</p>
    </div>
  );
}

/* ---------------- ACME gas flames ---------------- */
const GAS_COLOR: Record<string, string> = { Extinction: "rgb(var(--out))", Burned: "rgb(var(--burn))", "No Ignition": "rgb(var(--blow))" };
const GAS_LABEL: Record<string, string> = { Extinction: "self-extinguished (SE)", Burned: "burned until flow stopped (FT)", "No Ignition": "did not ignite" };

function GasSection() {
  const q = useQuery("gas-flames", client.gasFlames);
  const ms = useQuery("missions", client.missions);
  const pts = useMemo(() => (q.data ?? []).filter((r) => r.o2_pct && r.pressure_kpa)
    .map((r) => ({ x: Number(r.pressure_kpa), y: Number(r.o2_pct), end: r.outcome_basis === "not_recorded" ? "none" : r.outcome_class, r })), [q.data]);
  const hab = ms.data?.mars;
  const near = pts.filter((p) => p.y >= 30 && p.y <= 40 && p.x <= 80);
  return (
    <Card id="acme">
      <CardHeader eyebrow="ACME · gas-jet flames on the ISS" title="Flames at raised oxygen and low pressure" />
      <div className="space-y-3 p-5">
        {q.error ? <ErrorState message={q.error} onRetry={q.reload} /> : !q.data ? <Skeleton className="h-80" /> : (
          <>
            <ul className="flex flex-wrap gap-4 text-sm" aria-label="Legend">
              {Object.keys(GAS_LABEL).map((e) => <li key={e} className="flex items-center gap-2"><span className="h-3 w-3 rounded-full" style={{ background: GAS_COLOR[e] }} />CFI-G: {GAS_LABEL[e]}</li>)}
              <li className="flex items-center gap-2"><span className="h-3 w-3 rounded-full border-2" style={{ borderColor: "rgb(var(--muted))" }} />Flame Design: outcome not recorded</li>
              <li className="flex items-center gap-2"><span className="h-3 w-3 rotate-45 border-2" style={{ borderColor: "rgb(var(--danger))" }} />Moon/Mars habitat point</li>
            </ul>
            <div className="h-80" role="img" aria-label="ACME gas flame tests: pressure versus oxygen">
              <ResponsiveContainer>
                <ScatterChart margin={{ top: 10, right: 20, bottom: 24, left: 4 }}>
                  <CartesianGrid stroke="rgb(var(--line) / 0.5)" vertical={false} />
                  <XAxis type="number" dataKey="x" domain={[30, 340]} tick={{ fill: "rgb(var(--faint))", fontSize: 12 }} stroke="rgb(var(--line))"
                    label={{ value: "Pressure (kPa)", fill: "rgb(var(--faint))", fontSize: 12, position: "bottom", offset: 8 }} />
                  <YAxis type="number" dataKey="y" domain={[10, 90]} tick={{ fill: "rgb(var(--faint))", fontSize: 12 }} stroke="rgb(var(--line))" width={44}
                    label={{ value: "Oxygen %", fill: "rgb(var(--faint))", fontSize: 12, angle: -90, position: "insideLeft", offset: 12 }} />
                  <Tooltip content={<GasTip />} />
                  <Scatter data={pts.filter((p) => p.end === "none")} fill="rgb(var(--surface))" stroke="rgb(var(--muted))" strokeWidth={1.5} isAnimationActive={false} />
                  {Object.keys(GAS_COLOR).map((e) => <Scatter key={e} data={pts.filter((p) => p.end === e)} fill={GAS_COLOR[e]} isAnimationActive={false} />)}
                  {hab && <ReferenceDot x={hab.pressure_kpa} y={hab.o2_pct} r={8} fill="none" stroke="rgb(var(--danger))" strokeWidth={2}
                    label={{ value: "habitat", fill: "rgb(var(--danger))", fontSize: 12, position: "left" }} />}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <p className="text-sm text-muted">
              <b className="tnum text-ink">{near.length}</b> ACME tests ran at 30–40% O₂ and 80 kPa or below, around the habitat point. They are gas flames, not cabin
              materials, so StarryNight shows them as atmosphere evidence only. CFI-G pressure is NASA's approximate value.
            </p>
            <div className="flex flex-wrap gap-2">
              <SourceChip href={`${PSI_PORTAL}/PSI-159`} label="NASA PSI · ACME CFI-G (PSI-159)" />
              <SourceChip href={`${PSI_PORTAL}/PSI-10`} label="NASA PSI · ACME Flame Design (PSI-10)" />
            </div>
          </>
        )}
      </div>
    </Card>
  );
}

function GasTip({ active, payload }: { active?: boolean; payload?: { payload: { r: CsvRow } }[] }) {
  if (!active || !payload?.length) return null;
  const r = payload[0].payload.r;
  return (
    <div className="rounded-lg border border-line bg-surface p-3 text-sm shadow-card">
      <p className="font-mono text-ink">{r.test_id} · {r.fuel}</p>
      <p className="tnum text-muted">{r.o2_pct}% O₂ · {r.pressure_kpa} kPa · {r.investigation}</p>
      <p className="text-muted">{r.outcome_basis === "not_recorded" ? "outcome not recorded" : GAS_LABEL[r.outcome_class] ?? r.outcome_class}{r.burn_time_s ? ` · ${r.burn_time_s} s` : ""}</p>
    </div>
  );
}

/* ---------------- Session logs ---------------- */
function LogsSection() {
  const q = useQuery("session-logs", client.sessionLogs);
  const by = useMemo(() => {
    const m = new Map<string, CsvRow[]>();
    (q.data ?? []).forEach((r) => m.set(r.investigation, [...(m.get(r.investigation) ?? []), r]));
    return [...m.entries()];
  }, [q.data]);
  return (
    <Card id="logs">
      <CardHeader eyebrow="Session logs and indexes" title="PSI tables that log test days, not individual tests" />
      <div className="space-y-3 p-5">
        <p className="text-sm text-muted">Loaded so every PSI combustion table is in StarryNight. These rows are test days, figure lists or sampling sessions, so they are never counted as tests.</p>
        {q.error ? <ErrorState message={q.error} onRetry={q.reload} /> : !q.data ? <Skeleton className="h-40" /> : (
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full min-w-[620px] text-left text-sm">
              <thead className="eyebrow"><tr className="border-b border-line/60">{["Investigation", "Rows", "What a row is", "Flames ignited (sum)", "Fuels / samples"].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
              <tbody>
                {by.map(([inv, rows]) => {
                  const ign = rows.map((r) => Number(r.flames_ignited)).filter((x) => Number.isFinite(x) && x > 0);
                  return (
                    <tr key={inv} className="border-t border-line/40">
                      <td className="px-4 py-2 text-ink">{inv}</td>
                      <td className="tnum px-4 py-2">{rows.length}</td>
                      <td className="px-4 py-2 text-muted">{rows[0].row_type}</td>
                      <td className="tnum px-4 py-2">{ign.length ? ign.reduce((a, b) => a + b, 0) : "—"}</td>
                      <td className="max-w-[18rem] truncate px-4 py-2 text-muted" title={[...new Set(rows.map((r) => r.fuel))].join(", ")}>{[...new Set(rows.map((r) => r.fuel).filter(Boolean))].slice(0, 4).join(", ")}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Card>
  );
}

/* ---------------- FLEX-2 test matrix ---------------- */
function Flex2Section() {
  const q = useQuery("exp:PSI-68", () => client.experimentRows("PSI-68"));
  const rows = q.data?.records ?? [];
  return (
    <Card id="flex2">
      <CardHeader eyebrow="FLEX-2 · test matrix" title="Conditions NASA ran, per fuel" />
      <div className="space-y-3 p-5">
        <p className="text-sm text-muted">NASA's FLEX-2 table lists, for each fuel, the range of conditions used. It has no rows for individual tests and no outcomes, so StarryNight never counts these as tests.</p>
        {q.error ? <ErrorState message={q.error} onRetry={q.reload} /> : !q.data ? <Skeleton className="h-40" /> : (
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full min-w-[620px] text-left text-sm">
              <thead className="eyebrow"><tr className="border-b border-line/60">{["Fuel", "Gas", "O₂ levels %", "Pressure atm", "Flow cm/s", "Droplet mm"].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.record_id} className="border-t border-line/40">
                    <td className="px-4 py-2 text-ink">{r.fuel}</td><td className="px-4 py-2">{r.gas_mixtures}</td>
                    <td className="tnum px-4 py-2">{r.o2_levels_pct}</td><td className="tnum px-4 py-2">{r.pressure_levels_atm}</td>
                    <td className="tnum px-4 py-2">{r.flow_min_cm_s}–{r.flow_max_cm_s}</td><td className="tnum px-4 py-2">{r.droplet_diameter_min_mm}–{r.droplet_diameter_max_mm}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <SourceChip href={`${PSI_PORTAL}/PSI-68`} label="NASA PSI · FLEX-2 (PSI-68)" />
      </div>
    </Card>
  );
}

/* ---------------- SAME / SAME-R ---------------- */
function SmokeSection() {
  const q = useQuery("smoke", () => client.smoke());
  const rows = useMemo(() => {
    const m = new Map<string, CsvRow[]>();
    (q.data ?? []).forEach((r) => m.set(r.material, [...(m.get(r.material) ?? []), r]));
    return [...m.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [q.data]);
  const range = (rs: CsvRow[], k: string) => {
    const v = rs.map((x) => x[k]).filter((x) => x !== "" && x != null).map(Number).filter(Number.isFinite);
    return v.length ? (Math.min(...v) === Math.max(...v) ? `${Math.min(...v)}` : `${Math.min(...v)}–${Math.max(...v)}`) : "not recorded";
  };
  return (
    <Card id="smoke">
      <CardHeader eyebrow="SAME / SAME-R · smoke from overheated materials" title="What NASA heated, and under which conditions" />
      <div className="space-y-3 p-5">
        <p className="text-sm text-muted">The PSI tables list the test conditions for each run. The smoke particle results (size, concentration) are in NASA's raw data files on PSI.</p>
        {q.error ? <ErrorState message={q.error} onRetry={q.reload} /> : !q.data ? <Skeleton className="h-40" /> : (
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full min-w-[620px] text-left text-sm">
              <thead className="eyebrow"><tr className="border-b border-line/60">{["Material", "Runs (SAME / SAME-R)", "Air flow cm/s", "Heater ratio Rt/R0", "Aging time s"].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
              <tbody>
                {rows.map(([mat, rs]) => (
                  <tr key={mat} className="border-t border-line/40">
                    <td className="px-4 py-2 text-ink">{mat}</td>
                    <td className="tnum px-4 py-2">{rs.filter((x) => x.investigation === "SAME").length} / {rs.filter((x) => x.investigation === "SAME-R").length}</td>
                    <td className="tnum px-4 py-2">{range(rs, "flow_cm_s")}</td>
                    <td className="tnum px-4 py-2">{range(rs, "heater_resistance_ratio")}</td>
                    <td className="tnum px-4 py-2">{range(rs, "aging_time_s")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="flex flex-wrap gap-2">
          <SourceChip href={`${PSI_PORTAL}/PSI-102`} label="NASA PSI · SAME" />
          <SourceChip href={`${PSI_PORTAL}/PSI-101`} label="NASA PSI · SAME-R" />
        </div>
      </div>
    </Card>
  );
}

/* ---------------- SPICE ---------------- */
function SpiceSection() {
  const q = useQuery("gas-jets", client.gasJets);
  const rows = useMemo(() => {
    const m = new Map<string, CsvRow[]>();
    (q.data ?? []).forEach((r) => { const f = r.fuel.replace(/\s*%\s*/, "% "); m.set(f, [...(m.get(f) ?? []), r]); });
    return [...m.entries()].sort((a, b) => b[1].length - a[1].length);
  }, [q.data]);
  const span = (rs: CsvRow[], k: string) => {
    const v = rs.map((r) => r[k]).filter((x) => x !== "" && x != null).map(Number).filter(Number.isFinite);
    return v.length ? `${Math.min(...v)}–${Math.max(...v)}` : "—";
  };
  return (
    <Card id="spice">
      <CardHeader eyebrow="SPICE · gas-jet flames" title="Flame conditions studied for soot (smoke point)" />
      <div className="space-y-3 p-5">
        <p className="text-sm text-muted">Each row is one flame condition (fuel, nozzle, fuel rate, air speed). Useful context for how much soot and smoke a flame makes; not a material flammability test.</p>
        {q.error ? <ErrorState message={q.error} onRetry={q.reload} /> : !q.data ? <Skeleton className="h-40" /> : (
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="eyebrow"><tr className="border-b border-line/60">{["Fuel", "Conditions", "Air speed cm/s", "Fuel rate mg/s", "Nozzle mm"].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
              <tbody>
                {rows.map(([fuel, rs]) => (
                  <tr key={fuel} className="border-t border-line/40">
                    <td className="px-4 py-2 text-ink">{fuel}</td>
                    <td className="tnum px-4 py-2">{rs.length}</td>
                    <td className="tnum px-4 py-2">{span(rs, "air_velocity_cm_s")}</td>
                    <td className="tnum px-4 py-2">{span(rs, "fuel_rate_mg_s")}</td>
                    <td className="tnum px-4 py-2">{[...new Set(rs.map((r) => Number(r.nozzle_diameter_mm).toFixed(2)))].join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <SourceChip href={`${PSI_PORTAL}/PSI-107`} label="NASA PSI · SPICE (PSI-107)" />
      </div>
    </Card>
  );
}
