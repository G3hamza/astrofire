import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { Group as VGroup } from "@visx/group";
import { scaleLinear } from "@visx/scale";
import { ChevronDown, Table2 } from "lucide-react";
import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { BasisBadge, OutcomeTag } from "../components/badges";
import { FileRowChip, SourceChip } from "../components/SourceChip";
import { Card, CardHeader, EmptyState, ErrorState, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client, PSI_PORTAL } from "../lib/client";
import { OUTCOME_LABEL, outcomeKind, type OutcomeKind } from "../lib/domain";
import type { MapPoint } from "../lib/types";

/* Colors come from the CSS tokens (validated with the dataviz palette checker:
   burn/out/blow pass CVD + normal-vision separation on the dark surface). */
const C = {
  burn: "rgb(var(--burn))", out: "rgb(var(--out))", blow: "rgb(var(--blow))",
  grid: "rgb(var(--line) / 0.5)", axis: "rgb(var(--faint))", surface: "rgb(var(--surface))",
  danger: "rgb(var(--danger))", signal: "rgb(var(--signal))", muted: "rgb(var(--muted))",
};

export default function ChartsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-3xl space-y-3">
        <p className="kicker">Evidence charts</p>
        <h1 className="text-[2.2rem] font-semibold leading-tight tracking-tight text-ink sm:text-[2.6rem]">What NASA's fire data actually covers.</h1>
        <p className="max-w-3xl text-lg text-muted">Every point is a NASA space test from the PSI repository. Nothing here is modeled.</p>
      </header>
      <FlammabilityMap />
    </div>
  );
}

/* ================================ F5 Flammability map ================================ */

type Group = { o2: number; flow: number; kind: Exclude<OutcomeKind, "unknown">; observed: boolean; tests: MapPoint[] };

function FlammabilityMap() {
  const [material, setMaterial] = useState("");
  const all = useQuery("map:", () => client.map());
  const missions = useQuery("missions", client.missions);
  const [table, setTable] = useState(false);

  const materials = useMemo(() => {
    const c = new Map<string, number>();
    (all.data ?? []).forEach((p) => c.set(p.material, (c.get(p.material) ?? 0) + 1));
    return [...c.entries()].sort((a, b) => b[1] - a[1]);
  }, [all.data]);

  // Identical (O2, flow, outcome, basis) tests are drawn as ONE marker sized by count; tooltip lists them all.
  const groups = useMemo(() => {
    const m = new Map<string, Group>();
    for (const p of all.data ?? []) {
      if (material && p.material !== material) continue;
      const kind = outcomeKind(p.outcome);
      if (kind === "unknown") continue;
      const observed = p.outcome_basis === "observed";
      const k = `${p.o2_pct}|${p.flow_cm_s}|${kind}|${observed}`;
      const g = m.get(k) ?? { o2: p.o2_pct, flow: p.flow_cm_s, kind, observed, tests: [] };
      g.tests.push(p);
      m.set(k, g);
    }
    return [...m.values()];
  }, [all.data, material]);

  const n = groups.reduce((a, g) => a + g.tests.length, 0);
  const habitat = missions.data?.mars.o2_pct;
  const iss = missions.data?.iss.o2_pct;
  const maxO2 = Math.max(...(all.data ?? []).map((p) => p.o2_pct), 0);
  const yTop = Math.max(36, Math.ceil((habitat ?? 0) + 2));

  return (
    <Card>
      <CardHeader eyebrow="Flammability map (F5)" title="Where materials burned, went out or blew off in space"
        right={
          <div className="relative">
            <label htmlFor="mat" className="sr-only">Material</label>
            <select id="mat" value={material} onChange={(e) => setMaterial(e.target.value)}
              className="h-9 max-w-[11rem] appearance-none truncate rounded-full border border-line bg-raised pl-4 pr-8 text-sm text-ink focus:border-signal sm:max-w-none">
              <option value="">All materials ({all.data?.length ?? "…"})</option>
              {materials.map(([m, c]) => <option key={m} value={m}>{m} ({c})</option>)}
            </select>
            <ChevronDown size={14} className="pointer-events-none absolute right-2.5 top-2.5 text-muted" aria-hidden />
          </div>
        } />
      <div className="p-5">
        <Legend />
        {all.error ? <ErrorState message={all.error} onRetry={all.reload} />
          : !all.data ? <Skeleton className="h-[420px]" />
          : !groups.length ? <EmptyState title="No tests with oxygen + flow for this material" />
          : (
            <VisxMap groups={groups} habitat={habitat} iss={iss} maxO2={maxO2} yTop={yTop} n={n} />
          )}
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3 text-sm text-faint">
          <p>{n} tests with both oxygen and flow recorded. Hatched band: oxygen never tested in space. Filled = outcome written by NASA; hollow = inferred from notes.</p>
          <div className="flex gap-2">
            <SourceChip href={`${PSI_PORTAL}/PSI-25`} label="NASA PSI · BASS-II" />
            <button onClick={() => setTable(!table)} className="inline-flex h-8 items-center gap-1.5 rounded-full border border-line px-3 text-[12px] text-muted hover:text-ink">
              <Table2 size={13} aria-hidden /> {table ? "Hide table" : "Show as table"}
            </button>
          </div>
        </div>
        {table && <MapTable groups={groups} />}
      </div>
    </Card>
  );
}

type MarkerProps = { cx: number; cy: number; size?: number; payload: Group };

/** Shape = outcome (circle / triangle / diamond), fill = observed, hollow = inferred. Never color alone. */
function Marker({ cx: x, cy: y, payload }: MarkerProps) {
  const color = C[payload.kind === "burned" ? "burn" : payload.kind === "out" ? "out" : "blow"];
  const r = 5 + Math.min(9, Math.sqrt(payload.tests.length) * 2);
  // 2px surface ring separates overlapping markers; hollow (surface fill) = inferred.
  const ring = { fill: "none", stroke: C.surface, strokeWidth: 5, strokeLinejoin: "round" as const };
  const mark = { fill: payload.observed ? color : C.surface, stroke: color, strokeWidth: 2, strokeLinejoin: "round" as const };
  if (payload.kind === "out") {
    const pts = `${x},${y - r} ${x + r},${y + r * 0.8} ${x - r},${y + r * 0.8}`;
    return <g><polygon points={pts} {...ring} /><polygon points={pts} {...mark} /></g>;
  }
  if (payload.kind === "blowoff") {
    const pts = `${x},${y - r} ${x + r},${y} ${x},${y + r} ${x - r},${y}`;
    return <g><polygon points={pts} {...ring} /><polygon points={pts} {...mark} /></g>;
  }
  return <g><circle cx={x} cy={y} r={r} {...ring} /><circle cx={x} cy={y} r={r} {...mark} /></g>;
}

function MapTip({ g }: { g: Group }) {
  return (
    <div className="max-w-xs rounded-lg border border-line bg-surface p-3 text-sm shadow-card">
      <p className="tnum font-semibold text-ink">{g.o2}% O₂ · {g.flow} cm/s</p>
      <div className="my-1.5 flex flex-wrap gap-1.5"><OutcomeTag outcome={g.tests[0].outcome_class} /><BasisBadge basis={g.tests[0].outcome_basis} /></div>
      <p className="text-muted">{g.tests.length} test{g.tests.length > 1 ? "s" : ""}: <span className="font-mono text-ink">{g.tests.slice(0, 6).map((t) => t.test_id).join(", ")}{g.tests.length > 6 ? "…" : ""}</span></p>
      <p className="text-faint">{[...new Set(g.tests.map((t) => t.material))].join(", ")} · {g.tests[0].investigation}</p>
    </div>
  );
}

function MapTable({ groups }: { groups: Group[] }) {
  const rows = groups.flatMap((g) => g.tests).sort((a, b) => a.o2_pct - b.o2_pct || a.flow_cm_s - b.flow_cm_s);
  return (
    <div className="mt-4 max-h-80 overflow-auto rounded-lg border border-line">
      <table className="w-full text-left text-sm">
        <thead className="eyebrow sticky top-0 bg-surface"><tr>{["Test", "Material", "O₂ %", "Flow", "Outcome", "Basis", "Source"].map((h) => <th key={h} className="px-3 py-2 font-medium">{h}</th>)}</tr></thead>
        <tbody>
          {rows.map((p) => (
            <tr key={p.test_id} className="border-t border-line/40">
              <td className="px-3 py-1.5 font-mono">{p.test_id}</td><td className="px-3 py-1.5">{p.material}</td>
              <td className="tnum px-3 py-1.5">{p.o2_pct}</td><td className="tnum px-3 py-1.5">{p.flow_cm_s}</td>
              <td className="px-3 py-1.5"><OutcomeTag outcome={p.outcome_class} /></td><td className="px-3 py-1.5"><BasisBadge basis={p.outcome_basis} /></td>
              <td className="px-3 py-1.5"><FileRowChip file={p.source_file} row={p.source_row} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Legend() {
  const item = (kind: Exclude<OutcomeKind, "unknown">, shape: string) => (
    <li key={kind} className="flex items-center gap-2">
      <svg width="16" height="16" aria-hidden><Marker cx={8} cy={8} payload={{ kind, observed: true, tests: [], o2: 0, flow: 0 }} /></svg>
      <span className="text-ink">{OUTCOME_LABEL[kind]}</span><span className="text-faint">({shape})</span>
    </li>
  );
  return (
    <ul className="mb-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm" aria-label="Legend">
      {item("burned", "circle")}{item("out", "triangle")}{item("blowoff", "diamond")}
      <li className="flex items-center gap-2 text-muted"><span className="h-3 w-3 rounded-full bg-muted" />observed</li>
      <li className="flex items-center gap-2 text-muted"><span className="h-3 w-3 rounded-full border-2 border-muted" />inferred</li>
      <li className="flex items-center gap-2 text-muted">bigger = more tests at the same point</li>
    </ul>
  );
}

/* visx scatter: oxygen (y) vs air flow (x). Hatched band = oxygen never tested in space; habitat and ISS lines labelled. */
function VisxMap({ groups, habitat, iss, maxO2, yTop, n }: { groups: Group[]; habitat?: number; iss?: number; maxO2: number; yTop: number; n: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(0);
  const [hover, setHover] = useState<Group | null>(null);
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return;
    const m = () => setW(Math.floor(el.getBoundingClientRect().width)); m();
    const ro = new ResizeObserver(m); ro.observe(el); return () => ro.disconnect();
  }, []);
  const h = 440, mg = { top: 16, right: 20, bottom: 48, left: 56 };
  const iw = Math.max(10, w - mg.left - mg.right), ih = h - mg.top - mg.bottom;
  const maxFlow = Math.max(4, ...groups.map((g) => g.flow)) + 2;
  const x = scaleLinear<number>({ domain: [0, maxFlow], range: [0, iw], nice: true });
  const y = scaleLinear<number>({ domain: [12, yTop], range: [ih, 0] });
  const band = Math.ceil(maxO2 * 2) / 2;
  const order = [...groups].sort((a, b) => b.tests.length - a.tests.length);
  return (
    <div ref={ref} className="relative w-full" role="img" aria-label={`Scatter of ${n} NASA space tests: oxygen versus air flow, shaped by outcome`}>
      {w > 0 && (
        <svg width={w} height={h}>
          <defs>
            <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <rect width="10" height="10" style={{ fill: "rgb(var(--danger) / 0.04)" }} />
              <line x1="0" y1="0" x2="0" y2="10" style={{ stroke: "rgb(var(--danger) / 0.25)" }} strokeWidth="2" />
            </pattern>
          </defs>
          <VGroup left={mg.left} top={mg.top}>
            <GridRows scale={y} width={iw} stroke="rgb(var(--line))" strokeOpacity={0.5} strokeDasharray="2 4" />
            <rect x={0} y={y(yTop)} width={iw} height={Math.max(0, y(band) - y(yTop))} fill="url(#hatch)" />
            <text x={iw - 6} y={y(yTop) + 16} textAnchor="end" className="fill-danger font-mono" fontSize={11}>NEVER TESTED IN SPACE ABOVE {band}% O₂</text>
            {habitat != null && <>
              <line x1={0} x2={iw} y1={y(habitat)} y2={y(habitat)} stroke="rgb(var(--flare))" strokeDasharray="6 4" strokeWidth={1.5} />
              <text x={6} y={y(habitat) - 6} className="fill-flare font-mono" fontSize={11}>MOON / MARS HABITAT {habitat}% O₂ · 0 TESTS</text>
            </>}
            {iss != null && <>
              <line x1={0} x2={iw} y1={y(iss)} y2={y(iss)} stroke="rgb(var(--muted))" strokeDasharray="2 4" />
              <text x={iw - 6} y={y(iss) - 6} textAnchor="end" className="fill-muted font-mono" fontSize={11}>ISS AIR {iss}%</text>
            </>}
            {order.map((g, i) => (
              <g key={i} onMouseEnter={() => setHover(g)} onMouseLeave={() => setHover(null)} style={{ cursor: "pointer" }}>
                <Marker cx={x(g.flow)} cy={y(g.o2)} payload={g} />
              </g>
            ))}
            <AxisBottom top={ih} scale={x} stroke="rgb(var(--line))" tickStroke="rgb(var(--line))" numTicks={w < 520 ? 5 : 10}
              tickLabelProps={{ fill: "rgb(var(--muted))", fontSize: 11, fontFamily: "IBM Plex Mono", textAnchor: "middle" }}
              label="Air flow past the sample (cm/s)" labelProps={{ fill: "rgb(var(--muted))", fontSize: 12, textAnchor: "middle", fontFamily: "IBM Plex Sans" }} />
            <AxisLeft scale={y} stroke="rgb(var(--line))" tickStroke="rgb(var(--line))" numTicks={6} tickFormat={(v) => `${v}%`}
              tickLabelProps={{ fill: "rgb(var(--muted))", fontSize: 11, fontFamily: "IBM Plex Mono", textAnchor: "end", dx: -4, dy: 3 }}
              label="Oxygen" labelProps={{ fill: "rgb(var(--muted))", fontSize: 12, textAnchor: "middle", fontFamily: "IBM Plex Sans" }} />
          </VGroup>
        </svg>
      )}
      {hover && (
        <div className="pointer-events-none absolute z-10" style={{ left: Math.min(w - 300, mg.left + x(hover.flow) + 14), top: Math.max(0, mg.top + y(hover.o2) - 90) }}>
          <MapTip g={hover} />
        </div>
      )}
    </div>
  );
}
