import { ArrowRight, GitCompare, Plus, X } from "lucide-react";
import { useMemo, type ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ConfidenceBadge, EvidenceStatusBadge } from "../components/badges";
import { OutcomeBars } from "../components/charts/OutcomeBars";
import { SourceChip } from "../components/SourceChip";
import { MISSION_MEDIA } from "../lib/missionMedia";
import { Card, cx, ErrorState, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client } from "../lib/client";
import { outcomeKind, verdictTone } from "../lib/domain";
import type { MissionKey, ScenarioRequest, ScenarioResult } from "../lib/types";
import { scenarioQuery } from "./ScenarioPage";

const MISSIONS: MissionKey[] = ["iss", "exploration", "moon", "mars"];
const SHORT: Record<string, string> = { iss: "ISS", exploration: "Exploration", moon: "Moon", mars: "Mars", custom: "Custom" };
const NOMEX = "Aramid fabric (Nomex)";

/* Each column is one scenario, encoded in the URL as c=material~mission~o2~p~g~flow (shareable). */
function decode(c: string): ScenarioRequest {
  const [material, mission, o2, p, g, flow] = c.split("~");
  const n = (x: string | undefined, d: number) => (x !== undefined && x !== "" && Number.isFinite(Number(x)) ? Number(x) : d);
  return {
    material: material || NOMEX,
    mission: (MISSIONS as string[]).includes(mission) ? (mission as MissionKey) : null,
    o2_pct: n(o2, 21), pressure_kpa: n(p, 101.3), gravity_g: n(g, 0), flow_cm_s: n(flow, 5),
  };
}
const encode = (s: ScenarioRequest) =>
  [s.material, s.mission ?? "custom", s.o2_pct, s.pressure_kpa, s.gravity_g, s.flow_cm_s].join("~");

const PRESETS: { label: string; cols: ScenarioRequest[] }[] = [
  { label: "Nomex across every mission", cols: MISSIONS.map((m) => ({ material: NOMEX, mission: m, flow_cm_s: 5 })) },
  { label: "3 materials on Mars", cols: [NOMEX, "PMMA (acrylic)", "Cotton-fiberglass (SIBAL)"].map((m) => ({ material: m, mission: "mars" as MissionKey, flow_cm_s: 5 })) },
  { label: "PMMA: 21% vs 26% vs 31% O₂ (orbit, 55 kPa)", cols: [21, 26, 31].map((o) => ({ material: "PMMA (acrylic)", mission: null, o2_pct: o, pressure_kpa: 55, gravity_g: 0, flow_cm_s: 20 })) },
];

export default function ComparePage() {
  const [sp, setSp] = useSearchParams();
  const cols = useMemo(() => {
    const c = sp.getAll("c").map(decode);
    return c.length ? c : PRESETS[0].cols.map((x) => decode(encode({ o2_pct: 21, pressure_kpa: 101.3, gravity_g: 0, ...x })));
  }, [sp]);
  const families = useQuery("families", client.materialFamilies);
  const setCols = (next: ScenarioRequest[]) => {
    const q = new URLSearchParams();
    next.forEach((c) => q.append("c", encode(c)));
    setSp(q, { replace: true });
  };
  const update = (i: number, patch: Partial<ScenarioRequest>) => setCols(cols.map((c, j) => (j === i ? { ...c, ...patch } : c)));

  return (
    <div className="space-y-8">
      <header className="max-w-3xl space-y-3">
        <p className="kicker">Compare scenarios</p>
        <h1 className="text-[2.2rem] font-semibold leading-tight tracking-tight text-ink sm:text-[2.6rem]">Side by side: what changes, and why.</h1>
        <p className="text-lg text-muted">Up to four scenarios. Rows that differ are highlighted; every verdict links to its full evidence.</p>
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="font-mono text-[0.68rem] uppercase tracking-[0.16em] text-faint">Start from</span>
          {PRESETS.map((p) => (
            <button key={p.label} onClick={() => setCols(p.cols.map((x) => ({ o2_pct: 21, pressure_kpa: 101.3, gravity_g: 0, ...x })))}
              className="rounded-full border border-line px-3.5 py-1.5 text-sm text-muted transition-colors hover:border-ink/40 hover:text-ink">{p.label}</button>
          ))}
        </div>
      </header>

      <div className="overflow-x-auto">
        <div className="grid min-w-[720px] gap-4" style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(0, 1fr))${cols.length < 4 ? " 3.5rem" : ""}` }}>
          {cols.map((c, i) => (
            <ColumnEditor key={i} i={i} c={c} materials={families.data?.map((f) => f.material) ?? [c.material]}
              onChange={(p) => update(i, p)} onRemove={cols.length > 2 ? () => setCols(cols.filter((_, j) => j !== i)) : undefined} />
          ))}
          {cols.length < 4 && (
            <button onClick={() => setCols([...cols, { ...cols[cols.length - 1] }])} aria-label="Add a scenario"
              className="grid place-items-center rounded-card border border-dashed border-line text-muted hover:border-flare/60 hover:text-flare">
              <Plus size={20} />
            </button>
          )}
        </div>
      </div>

      <Results cols={cols} />
    </div>
  );
}

function ColumnEditor({ i, c, materials, onChange, onRemove }:
  { i: number; c: ScenarioRequest; materials: string[]; onChange: (p: Partial<ScenarioRequest>) => void; onRemove?: () => void }) {
  const opts = materials.includes(c.material) ? materials : [...materials, c.material];
  return (
    <Card className="overflow-hidden">
      <div className="relative h-28 bg-raised">
        {c.mission ? <img src={MISSION_MEDIA[c.mission].img} alt="" className="absolute inset-0 h-full w-full object-cover opacity-85" />
          : <div className="grid-bg absolute inset-0 opacity-60" aria-hidden />}
        <span className="absolute inset-0 bg-gradient-to-t from-surface via-surface/30 to-transparent" aria-hidden />
        <span className="absolute left-3 top-3 grid h-8 w-8 place-items-center rounded-full bg-flare font-semibold text-space">{String.fromCharCode(65 + i)}</span>
        {onRemove && <button onClick={onRemove} aria-label={`Remove scenario ${String.fromCharCode(65 + i)}`} className="absolute right-3 top-3 grid h-8 w-8 place-items-center rounded-full bg-black/60 text-ink hover:bg-black/80"><X size={15} /></button>}
        <span className="absolute bottom-2 left-3 text-lg font-semibold text-ink">{SHORT[c.mission ?? "custom"]}</span>
      </div>
      <div className="space-y-3 p-4">
      <select aria-label="Material" value={c.material} onChange={(e) => onChange({ material: e.target.value })}
        className="h-10 w-full rounded-full border border-line bg-raised px-3 text-sm text-ink">
        {opts.map((m) => <option key={m} value={m}>{m}</option>)}
      </select>
      <div className="flex flex-wrap gap-1" role="radiogroup" aria-label="Mission">
        {[...MISSIONS, "custom"].map((m) => {
          const on = (c.mission ?? "custom") === m;
          return (
            <button key={m} role="radio" aria-checked={on} onClick={() => onChange({ mission: m === "custom" ? null : (m as MissionKey) })}
              className={cx("rounded-full border px-2.5 py-1 text-[12px] font-medium", on ? "border-ink/30 bg-ink/10 text-ink" : "border-line text-muted hover:text-ink")}>
              {SHORT[m]}
            </button>
          );
        })}
      </div>
      {!c.mission && (
        <div className="grid grid-cols-3 gap-2">
          <Num label="O₂ %" v={c.o2_pct!} onChange={(v) => onChange({ o2_pct: v })} />
          <Num label="kPa" v={c.pressure_kpa!} onChange={(v) => onChange({ pressure_kpa: v })} />
          <Num label="g" v={c.gravity_g!} step={0.01} onChange={(v) => onChange({ gravity_g: v })} />
        </div>
      )}
      <Num label="Air flow cm/s" v={c.flow_cm_s!} onChange={(v) => onChange({ flow_cm_s: v })} />
      </div>
    </Card>
  );
}

function Num({ label, v, onChange, step = 0.5 }: { label: string; v: number; onChange: (v: number) => void; step?: number }) {
  return (
    <label className="block text-[12px] text-faint">
      {label}
      <input type="number" value={v} step={step} onChange={(e) => e.target.value !== "" && onChange(Number(e.target.value))}
        className="tnum mt-0.5 h-8 w-full rounded-md border border-line bg-raised px-2 text-sm text-ink" />
    </label>
  );
}

/* ------------------------------------------------------------------ */

function useScenario(c: ScenarioRequest) {
  const key = JSON.stringify(c);
  return useQuery<ScenarioResult>(`scenario:${key}`, () => client.scenario(c));
}

function Results({ cols }: { cols: ScenarioRequest[] }) {
  // Fixed max of 4 columns -> fixed number of hooks
  const r0 = useScenario(cols[0]); const r1 = useScenario(cols[1] ?? cols[0]);
  const r2 = useScenario(cols[2] ?? cols[0]); const r3 = useScenario(cols[3] ?? cols[0]);
  const qs = [r0, r1, r2, r3].slice(0, cols.length);
  const err = qs.find((q) => q.error);
  if (err) return <ErrorState message={err.error!} onRetry={err.reload} />;
  if (qs.some((q) => !q.data)) return <Skeleton className="h-96 rounded-card" />;
  const rs = qs.map((q) => q.data!);

  const rows: { label: string; cell: (r: ScenarioResult) => ReactNode; key: (r: ScenarioResult) => string }[] = [
    { label: "Verdict", key: (r) => r.verdict, cell: (r) => <VerdictCell v={r.verdict} /> },
    { label: "Evidence", key: (r) => r.evidence_status + r.confidence, cell: (r) => <div className="flex flex-col gap-1.5"><EvidenceStatusBadge status={r.evidence_status} /><ConfidenceBadge level={r.confidence} /></div> },
    { label: "Conditions", key: (r) => JSON.stringify(r.scenario), cell: (r) => <span className="tnum">{r.scenario.o2_pct}% O₂ · {r.scenario.pressure_kpa} kPa · {r.scenario.gravity_g} g · {r.scenario.flow_cm_s} cm/s</span> },
    { label: "Closest PSI tests", key: (r) => burned(r), cell: (r) => <span><b className="tnum">{burned(r)}</b> burned<div className="text-faint">{r.evidence.filter((e) => e.same_material).length} of {r.evidence.length} same material</div></span> },
    { label: "Why NASA can't answer", key: (r) => r.blockers.join("|"), cell: (r) => r.blockers.length
        ? <ul className="space-y-1">{r.blockers.map((b) => <li key={b} className="ml-4 list-disc text-ink/90 marker:text-danger">{b}</li>)}</ul>
        : <span className="text-ok">nothing blocking</span> },
    { label: "Closest space flame (same O₂ & pressure)", key: (r) => r.atmosphere_evidence?.find((a) => a.kind === "gas flame")?.test_id ?? "", cell: (r) => {
        const t = r.atmosphere_evidence?.find((a) => a.kind === "gas flame");
        return t ? (
          <div className="space-y-1">
            <div className="tnum text-ink">{t.o2_pct}% O₂ · {t.pressure_kpa} kPa</div>
            <div className="text-faint">{t.investigation} {t.fuel}: {t.test_end_raw === "SE" ? "self-extinguished" : t.test_end_raw === "FT" ? "burned until flow stopped" : t.outcome.toLowerCase()}</div>
            <SourceChip href={t.psi_url} label={`NASA PSI · ${t.test_id}`} />
          </div>
        ) : <span className="text-faint">none</span>;
      } },
  ];

  return (
    <div className="space-y-4">
      <ChangeSummary cols={cols} rs={rs} />
      <Card className="p-5 sm:p-6">
        <p className="kicker">Evidence profile</p>
        <p className="mb-4 mt-1 text-h3 text-ink">How the closest NASA tests ended, per scenario</p>
        <OutcomeBars rows={rs.map((r, i) => ({ name: `${String.fromCharCode(65 + i)} · ${SHORT[cols[i].mission ?? "custom"]}`, outcomes: r.evidence.map((e) => e.outcome) }))} />
      </Card>
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-line/60">
                <th scope="col" className="eyebrow w-44 px-4 py-3 font-medium">Compare</th>
                {cols.map((c, i) => (
                  <th key={i} scope="col" className="px-4 py-3 align-top">
                    {c.mission && <img src={MISSION_MEDIA[c.mission].img} alt="" className="mb-2 h-14 w-full rounded-lg object-cover opacity-80" />}
                    <span className="eyebrow">Scenario {String.fromCharCode(65 + i)}</span>
                    <div className="font-semibold text-ink">{c.material}</div>
                    <div className="text-muted">{SHORT[c.mission ?? "custom"]}</div>
                    <Link to={`/scenario?${scenarioQuery(c).toString()}`} className="mt-1 inline-flex items-center gap-1 text-[12px]">open full check <ArrowRight size={12} aria-hidden /></Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const differs = new Set(rs.map(row.key)).size > 1;
                return (
                  <tr key={row.label} className={cx("border-b border-line/40 align-top", differs && "bg-flare/[0.04]")}>
                    <th scope="row" className="px-4 py-3 font-medium text-muted">
                      {row.label}{differs && <span className="ml-1.5 rounded-full bg-flare/15 px-1.5 text-[10px] font-semibold uppercase text-flare" title="Differs between scenarios">differs</span>}
                    </th>
                    {rs.map((r, i) => <td key={i} className="px-4 py-3">{row.cell(r)}</td>)}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

const burned = (r: ScenarioResult) => `${r.evidence.filter((e) => outcomeKind(e.outcome) === "burned").length} of ${r.evidence.length}`;

function VerdictCell({ v }: { v: string }) {
  const tone = verdictTone(v);
  const cls = { burn: "text-burn", out: "text-out", caution: "text-caution", danger: "text-danger" }[tone];
  return <span className={cx("font-semibold", cls)}>{v}</span>;
}

/** Plain-language "what changed vs scenario A", built only from the API's blockers and verdicts. */
function ChangeSummary({ cols, rs }: { cols: ScenarioRequest[]; rs: ScenarioResult[] }) {
  const a = rs[0];
  const lines = rs.slice(1).map((r, i) => {
    const added = r.blockers.filter((b) => !a.blockers.includes(b));
    const removed = a.blockers.filter((b) => !r.blockers.includes(b));
    const name = `Scenario ${String.fromCharCode(66 + i)} (${cols[i + 1].material}, ${SHORT[cols[i + 1].mission ?? "custom"]})`;
    if (r.verdict === a.verdict && !added.length && !removed.length) return `${name}: same verdict and same limits as A.`;
    const parts = [r.verdict !== a.verdict ? `verdict changes to "${r.verdict}"` : `same verdict`];
    if (added.length) parts.push(`new limit: ${added.join(" ")}`);
    if (removed.length) parts.push(`limit removed: ${removed.join(" ")}`);
    return `${name}: ${parts.join("; ")}`;
  });
  return (
    <Card className="flex gap-3 p-5">
      <GitCompare size={20} className="mt-0.5 shrink-0 text-signal" aria-hidden />
      <div className="space-y-1.5">
        <p className="font-semibold text-ink">Compared with scenario A ({cols[0].material}, {SHORT[cols[0].mission ?? "custom"]}): <span className="font-normal text-muted">{a.verdict}</span></p>
        <ul className="space-y-1 text-ink/90">{lines.map((l) => <li key={l} className="ml-5 list-disc marker:text-signal">{l}</li>)}</ul>
      </div>
    </Card>
  );
}
