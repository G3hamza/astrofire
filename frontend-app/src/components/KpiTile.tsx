import type { ReactNode } from "react";
import { cx, NotAvailable, Skeleton } from "./ui";

/** Headline number. Value always comes from the API; null shows "not available". */
export function KpiTile({ label, value, unit, caption, source, tone = "default", loading }: {
  label: string;
  value: string | number | null | undefined;
  unit?: string;
  caption?: ReactNode;
  source?: ReactNode;
  tone?: "default" | "danger" | "signal";
  loading?: boolean;
}) {
  const valueCls = tone === "danger" ? "text-danger" : tone === "signal" ? "text-signal" : "text-ink";
  return (
    <div className={cx(
      "flex flex-col gap-2 rounded-card border bg-surface/90 p-5 shadow-card",
      tone === "danger" ? "border-danger/50" : "border-line",
    )}>
      <p className="eyebrow">{label}</p>
      {loading ? (
        <Skeleton className="h-10 w-28" />
      ) : (
        <p className={cx("tnum flex flex-wrap items-baseline gap-x-1.5 text-h1", valueCls)}>
          <span className="whitespace-nowrap">
          {value === null || value === undefined || value === "" ? <NotAvailable /> : value}</span>
          {unit && value !== null && value !== undefined && <span className="whitespace-nowrap text-lg font-medium text-muted">{unit}</span>}
        </p>
      )}
      {caption && <p className="text-sm text-muted">{caption}</p>}
      {source && <div className="mt-auto pt-1">{source}</div>}
    </div>
  );
}
