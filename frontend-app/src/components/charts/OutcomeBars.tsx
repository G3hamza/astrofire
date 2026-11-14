import { scaleLinear } from "@visx/scale";
import { useLayoutEffect, useRef, useState } from "react";
import { OUTCOME_LABEL, outcomeKind, type OutcomeKind } from "../../lib/domain";

/* For each scenario: how the closest NASA space tests ended (plain counts of tests; not a probability).
   Colors follow the outcome palette and every segment also carries a text label. */

const ORDER: OutcomeKind[] = ["burned", "out", "blowoff", "unknown"];
const FILL: Record<OutcomeKind, string> = { burned: "rgb(var(--burn))", out: "rgb(var(--out))", blowoff: "rgb(var(--blow))", unknown: "rgb(var(--unknown) / 0.55)" };

export type OutcomeRow = { name: string; outcomes: string[] };

export function OutcomeBars({ rows }: { rows: OutcomeRow[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return;
    const m = () => setW(Math.floor(el.getBoundingClientRect().width)); m();
    const ro = new ResizeObserver(m); ro.observe(el); return () => ro.disconnect();
  }, []);
  const maxN = Math.max(1, ...rows.map((r) => r.outcomes.length));
  const labelW = Math.min(220, Math.max(120, w * 0.28)), barH = 26, gap = 16;
  const x = scaleLinear<number>({ domain: [0, maxN], range: [0, Math.max(10, w - labelW - 16)] });
  const h = rows.length * (barH + gap);
  return (
    <div ref={ref} className="w-full">
      {w > 0 && (
        <svg width={w} height={h} role="img" aria-label="Outcomes of the closest NASA tests for each scenario">
          {rows.map((r, i) => {
            const y = i * (barH + gap);
            const counts = ORDER.map((k) => ({ k, n: r.outcomes.filter((o) => outcomeKind(o) === k).length })).filter((c) => c.n);
            let acc = 0;
            return (
              <g key={r.name} transform={`translate(0,${y})`}>
                <text x={0} y={barH / 2 + 4} className="fill-ink" fontSize={13}>{r.name}</text>
                <g transform={`translate(${labelW},0)`}>
                  <rect width={x(maxN)} height={barH} rx={6} style={{ fill: "rgb(var(--raised))" }} />
                  {counts.length === 0 && <text x={10} y={barH / 2 + 4} className="fill-faint font-mono" fontSize={11}>no nearby tests</text>}
                  {counts.map((c) => {
                    const x0 = x(acc); acc += c.n; const wd = x(acc) - x0;
                    return (
                      <g key={c.k}>
                        <rect x={x0} width={Math.max(0, wd - 2)} height={barH} rx={5} fill={FILL[c.k]} />
                        {wd > 64 && <text x={x0 + 8} y={barH / 2 + 4} fill="rgb(var(--space))" fontSize={11} fontWeight={600} className="font-mono">{c.n} {OUTCOME_LABEL[c.k].toLowerCase()}</text>}
                        {wd <= 64 && wd > 16 && <text x={x0 + wd / 2 - 1} y={barH / 2 + 4} textAnchor="middle" fill="rgb(var(--space))" fontSize={11} fontWeight={600} className="font-mono">{c.n}</text>}
                      </g>
                    );
                  })}
                </g>
              </g>
            );
          })}
        </svg>
      )}
      <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
        {ORDER.map((k) => <span key={k} className="inline-flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: FILL[k] }} aria-hidden />{OUTCOME_LABEL[k]}</span>)}
        <span className="text-faint">Counts of NASA tests, not a probability.</span>
      </div>
    </div>
  );
}
