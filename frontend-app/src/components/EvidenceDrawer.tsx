import { Database, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { api, useQuery } from "../lib/api";
import type { EvidenceRow } from "../lib/types";
import { BasisBadge, OutcomeTag } from "./badges";
import { FileRowChip, SourceChip } from "./SourceChip";
import { cx, ErrorState, NotAvailable, Skeleton } from "./ui";

type Experiments = { investigation_id: string; total: number; records: Record<string, string | null>[] };

/** Field order for the "full NASA row": identity, conditions, outcome, then everything else. */
const FIRST = ["record_id", "investigation", "test_number", "test_date", "sample_number", "material_original_name", "material_family",
  "classification_basis", "geometry", "thickness_mm", "gravity_g", "gravity_status", "o2_initial_pct", "o2_final_pct", "o2_status",
  "pressure_kpa", "pressure_status", "flow_start_cm_s", "flow_min_cm_s", "flow_cm_s", "flow_status", "outcome_class", "outcome_basis", "quality_status"];
const HIDE = new Set(["source_file", "source_row", "investigation_id", "material_id"]);

/** Slide-over with everything NASA recorded for one test, plus every link needed to verify it. */
export function EvidenceDrawer({ row, onClose }: { row: EvidenceRow | null; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const psiId = row?.psi_url.split("/").pop() ?? null;
  const exp = useQuery<Experiments>(psiId ? `experiments:${psiId}` : null,
    () => api<Experiments>(`/api/experiments?investigation_id=${psiId}&limit=1000`));
  const rec = exp.data?.records.find((r) => r.record_id === row?.test_id) ?? null;

  useEffect(() => {
    if (!row) return;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [row, onClose]);

  const keys = rec ? [...FIRST.filter((k) => k in rec), ...Object.keys(rec).filter((k) => !FIRST.includes(k) && !HIDE.has(k))] : [];

  return (
    <div className={cx("fixed inset-0 z-50 transition", row ? "pointer-events-auto" : "pointer-events-none")} aria-hidden={!row}>
      <div onClick={onClose} className={cx("absolute inset-0 bg-space/70 backdrop-blur-sm transition-opacity", row ? "opacity-100" : "opacity-0")} />
      <aside role="dialog" aria-modal="true" aria-labelledby="drawer-title"
        className={cx("absolute right-0 top-0 flex h-full w-full max-w-xl flex-col border-l border-line bg-surface shadow-2xl transition-transform duration-200",
          row ? "translate-x-0" : "translate-x-full")}>
        {row && (
          <>
            <header className="flex items-start justify-between gap-4 border-b border-line px-6 py-5">
              <div>
                <p className="eyebrow">NASA test record · {row.investigation}</p>
                <h2 id="drawer-title" className="font-mono text-h2 text-ink">{row.test_id}</h2>
                <div className="mt-2 flex flex-wrap gap-2"><OutcomeTag outcome={row.outcome} /><BasisBadge basis={row.outcome_basis} /></div>
              </div>
              <button ref={closeRef} onClick={onClose} aria-label="Close" className="grid h-9 w-9 place-items-center rounded-lg text-muted hover:bg-raised hover:text-ink">
                <X size={18} />
              </button>
            </header>

            <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
              <section className="space-y-2">
                <h3 className="eyebrow">Verify it</h3>
                <div className="flex flex-wrap gap-2">
                  <SourceChip href={row.psi_url} />
                  {row.doi && <SourceChip href={row.doi} />}
                  <FileRowChip file={row.source_file} row={row.source_row} />
                </div>
                <p className="text-sm text-faint">The file and row point to the original NASA PSI table in this repository (Bronze layer, unchanged).</p>
              </section>

              <section className="grid grid-cols-2 gap-3 text-sm">
                <Fact label="Material (as NASA wrote it)" value={row.material} wide />
                <Fact label="Identity" value={row.material_identity} wide />
                <Fact label="Oxygen" value={row.o2_pct != null ? `${row.o2_pct} %` : null} />
                <Fact label="Air flow" value={row.flow_cm_s != null ? `${row.flow_cm_s} cm/s` : null} />
                <Fact label="Gravity" value={`${row.gravity_g} g`} />
                <Fact label="Pressure" value={row.pressure_kpa != null ? `${row.pressure_kpa} kPa` : null} badge={row.pressure_status} />
              </section>

              {row.raw && (
                <section className="space-y-2">
                  <h3 className="eyebrow">NASA notes (raw)</h3>
                  <p className="rounded-lg border border-line bg-raised p-3 font-mono text-sm text-ink">{row.raw}</p>
                </section>
              )}

              <section className="space-y-2">
                <h3 className="eyebrow flex items-center gap-2"><Database size={13} aria-hidden /> Full cleaned NASA row</h3>
                {exp.error ? <ErrorState message={exp.error} onRetry={exp.reload} />
                  : exp.loading ? <div className="space-y-2">{[0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-6" />)}</div>
                  : !rec ? <p className="text-sm text-muted">Full row <NotAvailable /> for this investigation.</p>
                  : (
                    <dl className="divide-y divide-line/50 rounded-lg border border-line text-sm">
                      {keys.map((k) => (
                        <div key={k} className="grid grid-cols-[11rem_1fr] gap-3 px-3 py-1.5">
                          <dt className="font-mono text-[12px] text-faint">{k}</dt>
                          <dd className="break-words text-ink">{rec[k] ?? <span className="italic text-faint">not recorded</span>}</dd>
                        </div>
                      ))}
                    </dl>
                  )}
                {rec?.material_id && (
                  <Link to={`/materials/${rec.material_id}`} onClick={onClose} className="inline-block pt-1 text-sm">Open material page: {rec.material_id}</Link>
                )}
              </section>
            </div>
          </>
        )}
      </aside>
    </div>
  );
}

function Fact({ label, value, badge, wide }: { label: string; value: string | null; badge?: string; wide?: boolean }) {
  return (
    <div className={cx("rounded-lg border border-line bg-raised/50 p-3", wide && "col-span-2")}>
      <p className="eyebrow mb-1">{label}</p>
      <p className="flex flex-wrap items-center gap-2 text-ink">{value ?? <NotAvailable />}{badge && <BasisBadge basis={badge} />}</p>
    </div>
  );
}
