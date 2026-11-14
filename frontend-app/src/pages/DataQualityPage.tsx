import { Archive, ShieldCheck } from "lucide-react";
import { useMemo } from "react";
import { BasisBadge } from "../components/badges";
import { Card, CardHeader, cx, ErrorState, Skeleton } from "../components/ui";
import { useQuery } from "../lib/api";
import { client } from "../lib/client";
import { basisKind, type BasisKind } from "../lib/domain";

const BASIS_ORDER: BasisKind[] = ["observed", "inferred", "not_recorded"];
const BASIS_FILL: Record<string, string> = {
  observed: "bg-ok", inferred: "bg-caution", not_recorded: "bg-unknown/40",
};
const BASIS_TEXT: Record<string, string> = {
  observed: "written by NASA", inferred: "inferred from NASA notes", not_recorded: "not recorded",
};

export default function DataQualityPage() {
  const ov = useQuery("overview", client.overview);
  const dq = useQuery("data-quality", client.dataQuality);
  const mats = useQuery("materials", client.materials);

  // Outcome basis of solid space tests, exact counts per investigation (Gold outcome_summary)
  const basis = useMemo(() => {
    const per = new Map<string, Record<string, number>>();
    const tot: Record<string, number> = { observed: 0, inferred: 0, not_recorded: 0 };
    for (const o of ov.data?.outcomes ?? []) {
      const k = basisKind(o.outcome_basis);
      const n = Number(o.tests);
      const row = per.get(o.investigation) ?? { observed: 0, inferred: 0, not_recorded: 0 };
      row[k] = (row[k] ?? 0) + n; tot[k] = (tot[k] ?? 0) + n;
      per.set(o.investigation, row);
    }
    return { per: [...per.entries()], tot, total: Object.values(tot).reduce((a, b) => a + b, 0) };
  }, [ov.data]);

  const named = (mats.data ?? []).filter((m) => m.classification_basis === "explicit_name").length;
  const kpi = (n: string) => ov.data?.kpis.find((k) => k.kpi === n)?.value;

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <p className="eyebrow">Data quality</p>
        <h1 className="text-h1">How much of this is observed, inferred or missing</h1>
        <p className="max-w-3xl text-lg text-muted">StarryNight never hides weak data. Inferred values are always badged, and rejected rows are kept in quarantine, never deleted.</p>
      </header>

      {ov.error ? <ErrorState message={ov.error} onRetry={ov.reload} /> : (
        <Card>
          <CardHeader eyebrow="Outcome of each solid fire test" title={ov.data ? `${basis.total} space tests: who wrote the outcome?` : "Loading…"} />
          <div className="space-y-5 p-5">
            {!ov.data ? <Skeleton className="h-24" /> : (
              <>
                <Stacked parts={basis.tot} total={basis.total} big />
                <div className="space-y-2">
                  {basis.per.map(([inv, parts]) => {
                    const t = Object.values(parts).reduce((a, b) => a + b, 0);
                    return (
                      <div key={inv} className="grid grid-cols-[7rem_1fr_3.5rem] items-center gap-3 text-sm">
                        <span className="text-muted">{inv}</span>
                        <Stacked parts={parts} total={t} />
                        <span className="tnum text-right text-faint">{t}</span>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader eyebrow="Material identity" title="Was the material named?" />
          <div className="space-y-3 p-5 text-ink/90">
            {mats.data ? (
              <p><b className="tnum text-ok">{named}</b> of <b className="tnum">{mats.data.length}</b> materials are named in NASA tables. <b className="tnum text-caution">{mats.data.length - named}</b> are only a shape or color (e.g. "black rod"). Their family is a low-confidence guess.</p>
            ) : <Skeleton className="h-6" />}
            {kpi("pct_tests_material_named") && <p className="text-muted"><b className="tnum text-ink">{kpi("pct_tests_material_named")}%</b> of solid space tests used a named material.</p>}
          </div>
        </Card>
        <Card>
          <CardHeader eyebrow="Assumptions" title="Stated, never hidden" />
          <ul className="space-y-3 p-5 text-ink/90">
            <li className="flex items-start gap-3"><BasisBadge basis="assumed" /><span>Pressure of every ISS / Cygnus solid test is <b>assumed ~101.3 kPa</b>: the NASA tables don't record it. FLEX droplet pressure is measured.</span></li>
            <li className="flex items-start gap-3"><BasisBadge basis="inferred" /><span>Outcomes without an explicit "extinction" or "blowoff" are inferred as burned from NASA notes, and never used as labels.</span></li>
          </ul>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader eyebrow="Validation (Silver tables)" title="Rows that passed every rule" right={<ShieldCheck className="text-ok" size={22} aria-hidden />} />
          <div className="space-y-2 p-5">
            {dq.error ? <ErrorState message={dq.error} onRetry={dq.reload} /> : !dq.data ? <Skeleton className="h-48" /> : dq.data.tables.map((t) => (
              <div key={t.table} className="grid grid-cols-[9.5rem_1fr_6.5rem] items-center gap-3 text-sm">
                <span className="truncate font-mono text-[12px] text-muted">{t.table}</span>
                <Stacked parts={{ observed: Number(t.valid), inferred: Number(t.warnings) }} total={Number(t.records)} labels={{ observed: "valid", inferred: "warnings" }} />
                <span className="tnum text-right text-faint">{t.valid}/{t.records}</span>
              </div>
            ))}
            <p className="pt-2 text-sm text-faint">Green = valid · amber = kept with a warning.</p>
          </div>
        </Card>
        <Card>
          <CardHeader eyebrow="Quarantine" title="Rows flagged or rejected" right={<Archive className="text-muted" size={20} aria-hidden />} />
          {dq.data && (
            <table className="w-full text-left text-sm">
              <thead className="eyebrow"><tr className="border-b border-line/60">{["Investigation", "Rule", "Severity", "Rows"].map((h) => <th key={h} className="px-5 py-2 font-medium">{h}</th>)}</tr></thead>
              <tbody>
                {dq.data.quarantine.map((r) => (
                  <tr key={`${r.investigation}-${r.rule}`} className="border-t border-line/40">
                    <td className="px-5 py-2">{r.investigation}</td>
                    <td className="px-5 py-2 font-mono text-[12px] text-muted">{r.rule}</td>
                    <td className="px-5 py-2"><span className={cx("rounded px-1.5 py-0.5 text-[12px] font-semibold uppercase",
                      r.severity === "reject" ? "bg-danger/15 text-danger" : r.severity === "warn" ? "bg-caution/15 text-caution" : "bg-raised text-muted")}>{r.severity}</span></td>
                    <td className="tnum px-5 py-2">{r.records}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="px-5 py-3 text-sm text-faint">Full list with reasons: <code className="font-mono">data/quarantine/quarantine.csv</code>. Nothing is deleted.</p>
        </Card>
      </div>
    </div>
  );
}

/** Horizontal stacked bar; 2px surface gap between segments; text labels carry identity (not color alone). */
function Stacked({ parts, total, big, labels }: { parts: Record<string, number>; total: number; big?: boolean; labels?: Record<string, string> }) {
  const keys = BASIS_ORDER.filter((k) => (parts[k] ?? 0) > 0);
  return (
    <div className="space-y-2">
      <div className={cx("flex w-full gap-[2px] overflow-hidden rounded", big ? "h-8" : "h-4")} role="img"
        aria-label={keys.map((k) => `${labels?.[k] ?? BASIS_TEXT[k]}: ${parts[k]}`).join(", ")}>
        {keys.map((k) => (
          <div key={k} className={cx(BASIS_FILL[k], "h-full first:rounded-l last:rounded-r")} style={{ width: `${(parts[k] / Math.max(1, total)) * 100}%` }}
            title={`${labels?.[k] ?? BASIS_TEXT[k]}: ${parts[k]}`} />
        ))}
      </div>
      {big && (
        <ul className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          {keys.map((k) => (
            <li key={k} className="flex items-center gap-2">
              <span className={cx("h-3 w-3 rounded-sm", BASIS_FILL[k])} aria-hidden />
              <b className="tnum text-ink">{parts[k]}</b><span className="text-muted">{labels?.[k] ?? BASIS_TEXT[k]}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
