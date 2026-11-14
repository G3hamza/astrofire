import { Check, ChevronDown, CheckCircle2, Link2, MessageSquareText, SlidersHorizontal } from "lucide-react";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "react-router-dom";
import { BasisBadge, OutcomeTag } from "../components/badges";
import { DescribeScenario } from "../components/DescribeScenario";
import { EvidenceDrawer } from "../components/EvidenceDrawer";
import { InstrumentSlider } from "../components/InstrumentSlider";
import { MISSION_MEDIA } from "../lib/missionMedia";
import { AtmosphereEvidenceCard, ComingNextCard, GravityBoundsCard, WhyUntestedCard } from "../components/EvidenceContext";
import { FileRowChip, SourceChip } from "../components/SourceChip";
import { Callout, Card, CardHeader, cx, EmptyState, ErrorState, Skeleton } from "../components/ui";
import { VerdictBanner } from "../components/VerdictBanner";
import { useQuery } from "../lib/api";
import { client } from "../lib/client";
import { outcomeKind } from "../lib/domain";
import type { EvidenceRow, MissionKey, ScenarioRequest, ScenarioResult } from "../lib/types";

/* Scenario check, laid out in the SRS order (FR2.1-2.7):
   inputs -> verdict + confidence + evidence status -> "closest tests: X of Y burned" -> red blockers -> amber flags
   -> evidence table (test, investigation, material, O2, flow, outcome, basis, PSI link, file#row) -> extra context. */

const MISSION_ORDER: MissionKey[] = ["iss", "exploration", "moon", "mars"];
const DEFAULT_MATERIAL = "Aramid fabric (Nomex)";

/** URL <-> scenario. Shareable: /scenario?material=...&mission=mars&flow=5 */
export function readScenario(sp: URLSearchParams): ScenarioRequest {
  const mission = sp.get("mission");
  const num = (k: string, d: number) => { const v = Number(sp.get(k)); return sp.has(k) && Number.isFinite(v) ? v : d; };
  return {
    material: sp.get("material") || DEFAULT_MATERIAL,
    mission: mission && (MISSION_ORDER as string[]).includes(mission) ? (mission as MissionKey) : mission === "custom" ? null : "iss",
    o2_pct: num("o2", 21), pressure_kpa: num("p", 101.3), flow_cm_s: num("flow", 5), gravity_g: num("g", 0),
  };
}

export function scenarioQuery(s: ScenarioRequest) {
  const q = new URLSearchParams({ material: s.material, mission: s.mission ?? "custom", flow: String(s.flow_cm_s ?? 5) });
  if (!s.mission) { q.set("o2", String(s.o2_pct)); q.set("p", String(s.pressure_kpa)); q.set("g", String(s.gravity_g)); }
  return q;
}

export default function ScenarioPage() {
  const [sp, setSp] = useSearchParams();
  const req = useMemo(() => readScenario(sp), [sp]);
  const families = useQuery("families", client.materialFamilies);
  const missions = useQuery("missions", client.missions);
  const stats = useQuery("stats", client.stats);
  const map = useQuery("map:all", () => client.map());
  const flowRange = useMemo<[number, number] | null>(() => {
    const f = (map.data ?? []).map((d) => d.flow_cm_s).filter((v) => Number.isFinite(v));
    return f.length ? [Math.min(...f), Math.max(...f)] : null;
  }, [map.data]);

  // Debounced run on every change (sliders included). Requests take a few ms locally.
  const key = JSON.stringify(req);
  const [debounced, setDebounced] = useState(key);
  useEffect(() => { const t = setTimeout(() => setDebounced(key), 250); return () => clearTimeout(t); }, [key]);
  const res = useQuery<ScenarioResult>(`scenario:${debounced}`, () => client.scenario(JSON.parse(debounced)));
  const [drawer, setDrawer] = useState<EvidenceRow | null>(null);
  const closeDrawer = useCallback(() => setDrawer(null), []);

  const update = (patch: Partial<ScenarioRequest>) => setSp(scenarioQuery({ ...req, ...patch }), { replace: true });
  const m = req.mission && missions.data ? missions.data[req.mission] : null;
  const shown = { o2: m?.o2_pct ?? req.o2_pct!, p: m?.pressure_kpa ?? req.pressure_kpa!, g: m?.gravity_g ?? req.gravity_g! };
  // Moving any condition slider turns the preset into a custom scenario that starts from the preset's values.
  const setCondition = (patch: Partial<ScenarioRequest>) =>
    update({ mission: null, o2_pct: shown.o2, pressure_kpa: shown.p, gravity_g: shown.g, ...patch });

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-3xl space-y-3">
          <p className="kicker">Scenario check</p>
          <h1 className="text-[2.2rem] font-semibold leading-tight tracking-tight text-ink sm:text-[2.6rem]">Will it burn here, and what proves it?</h1>
          <p className="text-lg text-muted">Pick a mission, then fine-tune the conditions. The verdict comes from fixed rules over NASA's space tests, never from the AI.</p>
        </div>
        <ShareButton />
      </header>

      {/* ---------------- Mission presets (image cards) ---------------- */}
      <div role="radiogroup" aria-label="Mission preset" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {MISSION_ORDER.map((k) => {
          const on = req.mission === k; const mm = MISSION_MEDIA[k]; const md = missions.data?.[k];
          return (
            <button key={k} role="radio" aria-checked={on} onClick={() => update({ mission: k })}
              className={cx("group relative h-48 overflow-hidden rounded-card border text-left transition sm:h-auto sm:aspect-[16/11]",
                on ? "border-flare ring-2 ring-flare/40" : "border-line hover:border-ink/40")}>
              <img src={mm.img} alt={mm.alt} className={cx("absolute inset-0 h-full w-full object-cover transition duration-500", on ? "scale-105" : "opacity-80 group-hover:opacity-100")} />
              <span className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" aria-hidden />
              {on && <span className="absolute right-3 top-3 grid h-6 w-6 place-items-center rounded-full bg-flare text-space"><Check size={14} aria-hidden /></span>}
              <span className="absolute inset-x-3 bottom-3 space-y-1.5">
                <span className="block text-lg font-semibold text-ink">{mm.short}</span>
                <span className="hidden truncate text-xs text-ink/75 sm:block">{md?.name ?? ""}</span>
                <span className="flex flex-wrap gap-1 font-mono text-[0.68rem]">
                  {md && [md.gravity_g + " g", md.o2_pct + "% O₂", md.pressure_kpa + " kPa"].map((t) => (
                    <span key={t} className="rounded-full border border-ink/20 bg-black/55 px-2 py-0.5 text-ink">{t}</span>))}
                </span>
              </span>
            </button>
          );
        })}
      </div>
      <p className="-mt-5 flex flex-wrap items-center justify-between gap-2 font-mono text-[0.66rem] text-faint">
        <span className="flex items-center gap-1.5"><SlidersHorizontal size={12} aria-hidden /> {m ? "Preset: " + m.name : "Custom conditions (you moved a slider)"}</span>
        <span>Photos: {MISSION_ORDER.map((k) => MISSION_MEDIA[k].credit).join(" · ")}</span>
      </p>

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[340px_1fr]">
        {/* ---------------- Inputs ---------------- */}
        <Card className="space-y-6 p-5 lg:sticky lg:top-20">
          <Field label="Material" htmlFor="material">
            <div className="relative">
              <select id="material" value={req.material} onChange={(e) => update({ material: e.target.value })}
                className="h-11 w-full appearance-none rounded-full border border-line bg-raised pl-4 pr-9 text-ink focus:border-signal">
                {[...(families.data ?? []), ...(families.data?.some((f) => f.material === req.material) ? [] : [{ material: req.material, tests: 0 }])].map((f) => (
                  <option key={f.material} value={f.material}>{f.material}{f.tests ? " · " + f.tests + " space tests" : " · not in NASA space tests"}</option>
                ))}
              </select>
              <ChevronDown size={16} className="pointer-events-none absolute right-3 top-3.5 text-muted" aria-hidden />
            </div>
          </Field>

          <div className="space-y-5 border-t border-line/60 pt-5">
            <p className="flex items-center gap-2 font-mono text-[0.62rem] text-faint">
              <span className="inline-block h-2 w-4 rounded-full bg-ok/35 ring-1 ring-ok/50" aria-hidden /> range NASA tested with solid materials · click a marker to jump
            </p>
            <InstrumentSlider label="Oxygen" unit="% O₂" min={10} max={40} step={0.5} value={shown.o2} onChange={(v) => setCondition({ o2_pct: v })}
              tested={stats.data ? stats.data.o2_range_tested : null} markers={[{ at: 21, label: "ISS" }, { at: 34, label: "Habitat", tone: "flare" }]} />
            <InstrumentSlider label="Pressure" unit="kPa" min={30} max={110} step={0.5} value={shown.p} onChange={(v) => setCondition({ pressure_kpa: v })}
              tested={[101.3, 101.3]} testedLabel="assumed cabin pressure" markers={[{ at: 56.5, label: "Habitat", tone: "flare" }, { at: 101.3, label: "ISS" }]} />
            <InstrumentSlider label="Gravity" unit="g" min={0} max={1} step={0.01} value={shown.g} onChange={(v) => setCondition({ gravity_g: v })}
              tested={[0, 0]} testedLabel="tested gravity (~0 g)"
              markers={[{ at: 0, label: "Orbit" }, { at: 0.166, label: "Moon", tone: "flare" }, { at: 0.38, label: "Mars", tone: "flare" }, { at: 1, label: "Earth" }]} />
            <InstrumentSlider label="Air flow" unit="cm/s" min={0} max={40} step={0.5} value={req.flow_cm_s!} onChange={(v) => update({ flow_cm_s: v })}
              tested={flowRange} />
            <p className="text-[12px] text-faint">Moving oxygen, pressure or gravity switches the preset to custom conditions.</p>
          </div>

          <details open className="group border-t border-line/60 pt-4">
            <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-medium text-signal">
              <MessageSquareText size={15} aria-hidden /> Describe it in your own words
              <ChevronDown size={14} className="ml-auto transition group-open:rotate-180" aria-hidden />
            </summary>
            <div className="mt-3">
              <DescribeScenario compact onParsed={(r) => setSp(scenarioQuery({ ...r.scenario, mission: r.scenario.mission ?? null }))} />
            </div>
          </details>
        </Card>

        {/* ---------------- Result ---------------- */}
        <div className="min-w-0 space-y-4" aria-live="polite">
          {res.error ? <ErrorState message={res.error} onRetry={res.reload} />
            : !res.data ? <ResultSkeleton />
            : <ScenarioResultView r={res.data} stale={res.loading || debounced !== key} onSelect={setDrawer} />}
        </div>
      </div>
      <EvidenceDrawer row={drawer} onClose={closeDrawer} />
    </div>
  );
}

function ShareButton() {
  const [done, setDone] = useState(false);
  return (
    <button onClick={() => navigator.clipboard?.writeText(window.location.href).then(() => { setDone(true); setTimeout(() => setDone(false), 1500); }).catch(() => undefined)}
      className="inline-flex h-10 items-center gap-2 rounded-full border border-line px-4 text-sm text-ink hover:border-ink/40">
      {done ? <Check size={16} className="text-ok" aria-hidden /> : <Link2 size={16} aria-hidden />}
      {done ? "Link copied" : "Copy link to this scenario"}
    </button>
  );
}

/* ====================================================================================== */

export function ScenarioResultView({ r, stale, onSelect }: { r: ScenarioResult; stale?: boolean; onSelect?: (e: EvidenceRow) => void }) {
  const burned = r.evidence.filter((e) => outcomeKind(e.outcome) === "burned").length;
  const same = r.evidence.filter((e) => e.same_material).length;
  const extra = (r.why_untested?.length ?? 0) + (r.atmosphere_evidence?.length ?? 0) + (r.gravity_bounds ? 1 : 0);
  return (
    <div className={cx("space-y-4 transition-opacity", stale && "opacity-60")}>
      {/* FR2.2 verdict + confidence + evidence status */}
      <VerdictBanner verdict={r.verdict} confidence={r.confidence} evidenceStatus={r.evidence_status} />

      {/* FR2.7 never a percentage */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 rounded-card border border-line bg-surface px-4 py-3 font-mono text-[0.8rem] text-muted">
        {r.evidence.length > 0 && (
          <span title={r.nearby_burn_share_note}>
            Closest tests: <b className="tnum text-base text-ink">{burned} of {r.evidence.length} burned</b>
            <span className="text-faint"> · {same} of {r.evidence.length} same material · a count of tests, not a probability</span>
          </span>
        )}
        <span className="tnum">Conditions: <b className="text-ink">{r.scenario.o2_pct}% O₂ · {r.scenario.pressure_kpa} kPa · {r.scenario.gravity_g} g · {r.scenario.flow_cm_s} cm/s</b></span>
      </div>

      {/* FR2.3 red blockers, FR2.4 amber flags */}
      {r.blockers.length > 0 && <Callout tone="danger" title="Why NASA can't answer this yet" items={r.blockers} />}
      {r.flags.length > 0 && <Callout tone="caution" title="Notes on the evidence" items={r.flags} />}

      {/* FR2.5 evidence table */}
      <EvidenceTable rows={r.evidence} onSelect={onSelect} />

      {extra > 0 && (
        <details open className="group space-y-4">
          <summary className="flex cursor-pointer list-none items-center gap-2 py-1 text-h3">
            More context from NASA's PSI data
            <ChevronDown size={16} className="text-muted transition group-open:rotate-180" aria-hidden />
          </summary>
          <div className="mt-3 space-y-4">
            <GravityBoundsCard b={r.gravity_bounds} />
            <WhyUntestedCard items={r.why_untested ?? []} />
            {(r.why_untested ?? []).some((w) => w.topic !== "gravity") && <AtmosphereEvidenceCard rows={r.atmosphere_evidence ?? []} />}
            {r.gravity_bounds && <ComingNextCard items={r.gravity_bounds.coming_next} />}
          </div>
        </details>
      )}
    </div>
  );
}

export function EvidenceTable({ rows, onSelect }: { rows: EvidenceRow[]; onSelect?: (r: EvidenceRow) => void }) {
  if (!rows.length) return <EmptyState title="No NASA tests to show" hint="No solid-material space test has conditions near this scenario." />;
  return (
    <Card>
      <CardHeader eyebrow="What proves it" title={`${rows.length} closest NASA space tests`}
        right={<span className="hidden text-sm text-faint sm:block">click a test ID for the full NASA record</span>} />
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead className="eyebrow">
            <tr className="border-b border-line/60">
              {["Test ID", "Investigation", "Material", "O₂ %", "Flow cm/s", "Outcome", "Outcome basis", "NASA PSI", "File # row"].map((h) => (
                <th key={h} scope="col" className="whitespace-nowrap px-3 py-3 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.test_id} className="border-b border-line/40 align-top hover:bg-raised/50">
                <td className="whitespace-nowrap px-3 py-3">
                  {onSelect
                    ? <button onClick={() => onSelect(e)} className="font-mono text-signal hover:underline">{e.test_id}</button>
                    : <span className="font-mono text-ink">{e.test_id}</span>}
                </td>
                <td className="whitespace-nowrap px-3 py-3 text-ink">{e.investigation}</td>
                <td className="max-w-[14rem] px-3 py-3">
                  <div className="truncate text-ink" title={e.material}>{e.material}</div>
                  <div className="flex items-center gap-1 text-faint">
                    {e.same_material && <CheckCircle2 size={12} className="text-ok" aria-hidden />}
                    {e.same_material ? "same material" : e.material_family}
                    {e.material_identity.startsWith("not named") && <span className="text-caution"> · family inferred</span>}
                  </div>
                </td>
                <td className="tnum whitespace-nowrap px-3 py-3">{e.o2_pct ?? "–"}</td>
                <td className="tnum whitespace-nowrap px-3 py-3">{e.flow_cm_s ?? "–"}</td>
                <td className="px-3 py-3"><OutcomeTag outcome={e.outcome} /></td>
                <td className="px-3 py-3"><BasisBadge basis={e.outcome_basis} /></td>
                <td className="px-3 py-3"><SourceChip href={e.psi_url} /></td>
                <td className="px-3 py-3"><FileRowChip file={e.source_file} row={e.source_row} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="border-t border-line/60 px-4 py-2 text-[12px] text-faint">Pressure of these ISS/Cygnus tests is assumed ~101 kPa (not recorded in the PSI tables).</p>
    </Card>
  );
}

/* ---------------- small pieces ---------------- */
function Field({ label, htmlFor, children }: { label: string; htmlFor?: string; children: ReactNode }) {
  return (
    <div className="space-y-2">
      <label htmlFor={htmlFor} className="eyebrow block">{label}</label>
      {children}
    </div>
  );
}

function ResultSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-28 rounded-card" />
      <Skeleton className="h-10" />
      <Skeleton className="h-64 rounded-card" />
    </div>
  );
}
