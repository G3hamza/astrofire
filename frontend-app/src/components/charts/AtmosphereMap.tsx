import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridColumns, GridRows } from "@visx/grid";
import { Group } from "@visx/group";
import { scaleLinear } from "@visx/scale";
import { useLayoutEffect, useMemo, useRef, useState } from "react";
import { cx } from "../ui";

/* Oxygen x pressure map of every NASA PSI space flame that has both values, vs the habitat design atmosphere.
   Honest by construction: solid-material tests have no recorded pressure, so they sit on the assumed-cabin line and
   are labelled as such; nothing is interpolated, every point keeps its NASA test id and source. */

export type AtmPoint = { id: string; kind: "solid" | "droplet" | "gas"; o2: number; p: number; label: string; outcome: string; url: string };
type Series = { key: AtmPoint["kind"]; name: string; note: string };

const SERIES: Series[] = [
  { key: "solid", name: "Solid materials", note: "BASS, BASS-II, Saffire · pressure not recorded, cabin 101.3 kPa assumed" },
  { key: "droplet", name: "Fuel droplets", note: "FLEX · measured pressure" },
  { key: "gas", name: "Gas flames", note: "ACME · measured pressure" },
];
const HABITAT = { o2: 34, p: 56.5 };
const CHALLENGE = { o2Min: 30, pMax: 70.3 };

function Mark({ kind, x, y, active }: { kind: AtmPoint["kind"]; x: number; y: number; active?: boolean }) {
  const r = active ? 5 : 3;
  if (kind === "solid") return <rect x={x - r} y={y - r} width={r * 2} height={r * 2} fill="rgb(var(--ink))" opacity={active ? 1 : 0.75} />;
  if (kind === "droplet") return <circle cx={x} cy={y} r={r} fill="rgb(var(--signal))" opacity={active ? 1 : 0.7} />;
  return <circle cx={x} cy={y} r={r + 0.5} fill="none" stroke="rgb(var(--out))" strokeWidth={1.2} opacity={active ? 1 : 0.6} />;
}

function Chart({ width, points }: { width: number; points: AtmPoint[] }) {
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [hover, setHover] = useState<AtmPoint | null>(null);
  const [focus, setFocus] = useState(true);
  const height = Math.max(320, Math.min(460, width * 0.55));
  const m = { top: 24, right: 24, bottom: 52, left: 60 };
  const iw = width - m.left - m.right, ih = height - m.top - m.bottom;
  const maxO2 = focus ? 60 : Math.max(45, ...points.map((d) => d.o2)) + 2;
  const maxP = focus ? 125 : Math.max(110, ...points.map((d) => d.p)) + 8;
  const x = useMemo(() => scaleLinear<number>({ domain: [0, maxO2], range: [0, iw], nice: true }), [maxO2, iw]);
  const y = useMemo(() => scaleLinear<number>({ domain: [0, maxP], range: [ih, 0], nice: true }), [maxP, ih]);
  const inView = (d: AtmPoint) => d.o2 <= maxO2 && d.p <= maxP;
  const shown = points.filter((d) => !hidden.has(d.kind) && inView(d));
  const outside = points.filter((d) => !hidden.has(d.kind) && !inView(d)).length;
  const counts = Object.fromEntries(SERIES.map((s) => [s.key, points.filter((d) => d.kind === s.key).length]));
  const toggle = (k: string) => setHidden((h) => { const n = new Set(h); n.has(k) ? n.delete(k) : n.add(k); return n; });

  const cx0 = x(CHALLENGE.o2Min), cy0 = y(CHALLENGE.pMax);
  const narrow = width < 560, boxW = narrow ? 196 : 262;
  const lx0 = x(HABITAT.o2) + 20 + boxW > iw ? x(HABITAT.o2) - 20 - boxW : x(HABITAT.o2) + 20;
  const lx = Math.max(-m.left + 4, Math.min(iw - boxW, lx0));
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
      <div className="mr-auto inline-flex rounded-full border border-line p-0.5" role="group" aria-label="Chart range">
        {[["Habitat range", true], ["All pressures", false]].map(([label, f]) => (
          <button key={String(label)} type="button" aria-pressed={focus === f} onClick={() => setFocus(f as boolean)}
            className={cx("rounded-full px-3 py-1 text-sm transition-colors", focus === f ? "bg-ink/10 text-ink" : "text-muted hover:text-ink")}>{label}</button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Show or hide data series">
        {SERIES.map((s) => (
          <button key={s.key} type="button" aria-pressed={!hidden.has(s.key)} onClick={() => toggle(s.key)} title={s.note}
            className={cx("inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors",
              hidden.has(s.key) ? "border-line text-faint line-through" : "border-line/80 bg-raised/60 text-ink")}>
            <svg width="12" height="12" aria-hidden><Mark kind={s.key} x={6} y={6} /></svg>
            {s.name} <span className="font-mono text-xs text-muted">{counts[s.key]}</span>
          </button>
        ))}
      </div>
      </div>
      <div className="relative">
        <svg width={width} height={height} role="img"
          aria-label={`Oxygen versus pressure for ${points.length} NASA space flame tests. The habitat design point at ${HABITAT.o2}% oxygen and ${HABITAT.p} kPa has no solid-material test.`}>
          <Group left={m.left} top={m.top}>
            <GridRows scale={y} width={iw} stroke="rgb(var(--line))" strokeOpacity={0.5} strokeDasharray="2 4" />
            <GridColumns scale={x} height={ih} stroke="rgb(var(--line))" strokeOpacity={0.5} strokeDasharray="2 4" />
            {/* challenge region: >= 30% O2 at <= 70.3 kPa */}
            <rect x={cx0} y={cy0} width={Math.max(0, iw - cx0)} height={Math.max(0, ih - cy0)} style={{ fill: "rgb(var(--flare) / 0.06)" }}
              stroke="rgb(var(--flare) / 0.55)" strokeDasharray="5 4" />
            <text x={iw - 8} y={ih - 10} textAnchor="end" className="fill-flare font-mono" fontSize={11}>CHALLENGE RANGE · ≥30% O₂ · ≤70.3 kPa</text>
            {/* assumed cabin pressure line for solid tests */}
            <line x1={0} x2={iw} y1={y(101.3)} y2={y(101.3)} stroke="rgb(var(--ink) / 0.25)" />
            <text x={4} y={y(101.3) - 8} className="fill-muted font-mono" fontSize={10.5}>{narrow ? "CABIN 101.3 kPa (ASSUMED)" : "CABIN 101.3 kPa · SOLID-TEST PRESSURE ASSUMED"}</text>
            {shown.map((d) => (
              <g key={d.kind + d.id} onMouseEnter={() => setHover(d)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(d)} onBlur={() => setHover(null)}
                tabIndex={-1} style={{ cursor: "pointer" }}>
                <Mark kind={d.kind} x={x(d.o2)} y={y(d.p)} active={hover === d} />
              </g>
            ))}
            {/* habitat design point */}
            <g transform={`translate(${x(HABITAT.o2)},${y(HABITAT.p)})`}>
              <circle r={11} fill="none" stroke="rgb(var(--flare))" strokeWidth={1.5} />
              <line x1={-18} x2={-13} stroke="rgb(var(--flare))" /><line x1={13} x2={18} stroke="rgb(var(--flare))" />
              <line y1={-18} y2={-13} stroke="rgb(var(--flare))" /><line y1={13} y2={18} stroke="rgb(var(--flare))" />
              <circle r={2.5} fill="rgb(var(--flare))" />
            </g>
            <rect x={lx} y={y(HABITAT.p) - 34} width={boxW} height={40} rx={6} style={{ fill: "rgb(var(--space) / 0.88)" }} stroke="rgb(var(--flare) / 0.5)" />
            <text x={lx + 10} y={y(HABITAT.p) - 18} className="fill-ink font-mono" fontSize={11.5}>
              {narrow ? `HABITAT · ${HABITAT.o2}% · ${HABITAT.p} kPa` : `MOON / MARS HABITAT · ${HABITAT.o2}% · ${HABITAT.p} kPa`}
            </text>
            <text x={lx + 10} y={y(HABITAT.p) - 3} className="fill-danger font-mono" fontSize={11}>0 solid-material tests here</text>
            <AxisBottom top={ih} scale={x} stroke="rgb(var(--line))" tickStroke="rgb(var(--line))" numTicks={width < 520 ? 5 : 10}
              tickLabelProps={{ fill: "rgb(var(--muted))", fontSize: 11, fontFamily: "IBM Plex Mono", textAnchor: "middle" }}
              label="Oxygen in the atmosphere (% by volume)" labelProps={{ fill: "rgb(var(--muted))", fontSize: 12, textAnchor: "middle", fontFamily: "IBM Plex Sans" }} />
            <AxisLeft scale={y} stroke="rgb(var(--line))" tickStroke="rgb(var(--line))" numTicks={6}
              tickLabelProps={{ fill: "rgb(var(--muted))", fontSize: 11, fontFamily: "IBM Plex Mono", textAnchor: "end", dx: -4, dy: 3 }}
              label="Pressure (kPa)" labelProps={{ fill: "rgb(var(--muted))", fontSize: 12, textAnchor: "middle", fontFamily: "IBM Plex Sans" }} />
          </Group>
        </svg>
        {hover && (
          <div className="pointer-events-none absolute z-10 w-64 rounded-lg border border-line bg-surface p-3 text-sm shadow-card"
            style={{ left: Math.min(width - 270, m.left + x(hover.o2) + 12), top: Math.max(0, m.top + y(hover.p) - 70) }}>
            <p className="font-mono text-xs text-muted">{hover.id}</p>
            <p className="font-medium text-ink">{hover.label}</p>
            <p className="readout text-muted">{hover.o2}% O₂ · {hover.p} kPa{hover.kind === "solid" ? " (assumed)" : ""}</p>
            <p className="text-muted">Outcome: {hover.outcome || "not recorded"}</p>
          </div>
        )}
      </div>
      {outside > 0 && <p className="font-mono text-[0.7rem] text-faint">{outside} tests sit outside this range (higher oxygen or pressure). Choose "All pressures" to see them.</p>}
    </div>
  );
}

/** Measures its own width on mount and on every resize (no reliance on a first ResizeObserver callback). */
export function AtmosphereMap({ points }: { points: AtmPoint[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return;
    const measure = () => setWidth(Math.floor(el.getBoundingClientRect().width));
    measure();
    const ro = new ResizeObserver(measure); ro.observe(el);
    window.addEventListener("resize", measure);
    return () => { ro.disconnect(); window.removeEventListener("resize", measure); };
  }, []);
  return <div ref={ref} className="w-full">{width > 0 ? <Chart width={width} points={points} /> : <div className="h-[380px]" />}</div>;
}
