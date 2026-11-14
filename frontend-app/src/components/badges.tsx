import { Asterisk, Ban, CircleHelp, Eye, FileSearch, Flame, Gauge, Wind } from "lucide-react";
import type { ReactNode } from "react";
import { basisKind, OUTCOME_LABEL, outcomeKind, type BasisKind, type OutcomeKind } from "../lib/domain";
import { cx } from "./ui";

/* Every status uses icon + text + color, never color alone (NFR6). */

function Pill({ className, icon, children, title }: { className: string; icon: ReactNode; children: ReactNode; title?: string }) {
  return (
    <span title={title} className={cx("inline-flex h-6 items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 text-sm font-medium", className)}>
      {icon}
      {children}
    </span>
  );
}

/* ---------- Outcome ---------- */
const OUTCOME_STYLE: Record<OutcomeKind, { cls: string; Icon: typeof Flame }> = {
  burned: { cls: "bg-burn/15 text-burn ring-1 ring-burn/40", Icon: Flame },
  out: { cls: "bg-out/15 text-out ring-1 ring-out/40", Icon: Ban },
  blowoff: { cls: "bg-blow/15 text-blow ring-1 ring-blow/40", Icon: Wind },
  unknown: { cls: "bg-unknown/10 text-unknown ring-1 ring-unknown/30", Icon: CircleHelp },
};

/** Shows the normalized outcome; when NASA used a more specific word (e.g. "Extinction") it is kept as a tooltip + suffix. */
export function OutcomeTag({ outcome, showRaw = true }: { outcome: string | null | undefined; showRaw?: boolean }) {
  const k = outcomeKind(outcome);
  const { cls, Icon } = OUTCOME_STYLE[k];
  const label = OUTCOME_LABEL[k];
  const raw = outcome && outcome.toLowerCase() !== label.toLowerCase() && outcome.toLowerCase() !== "went out" ? outcome : null;
  return (
    <Pill className={cls} icon={<Icon size={14} aria-hidden />} title={raw ? `NASA term: ${raw}` : undefined}>
      {label}
      {showRaw && raw && <span className="font-normal opacity-75">· {raw}</span>}
    </Pill>
  );
}

/* ---------- Evidence basis: observed / inferred / assumed ---------- */
const BASIS: Record<BasisKind, { cls: string; Icon: typeof Eye; label: string; help: string }> = {
  observed: { cls: "bg-ok/15 text-ok ring-1 ring-ok/45", Icon: Eye, label: "Observed", help: "NASA wrote this value in the test table." },
  inferred: { cls: "text-caution border border-dashed border-caution/60 bg-transparent", Icon: FileSearch, label: "Inferred", help: "Derived from NASA notes; NASA did not write it explicitly." },
  assumed: { cls: "text-muted border border-dotted border-muted/70 bg-transparent", Icon: Asterisk, label: "Assumed", help: "Not in the NASA table; a stated assumption (e.g. ISS cabin pressure ~101 kPa)." },
  not_recorded: { cls: "text-faint border border-line bg-transparent", Icon: CircleHelp, label: "Not recorded", help: "NASA did not record this." },
};

export function BasisBadge({ basis }: { basis: string | BasisKind | null | undefined }) {
  const k = basisKind(basis);
  const { cls, Icon, label, help } = BASIS[k];
  return (
    <Pill className={cls} icon={<Icon size={13} aria-hidden />} title={help}>
      {label}
    </Pill>
  );
}

/* ---------- Confidence + evidence status ---------- */
export function ConfidenceBadge({ level }: { level: string }) {
  const l = level.toLowerCase();
  const filled = l === "high" ? 3 : l === "medium" ? 2 : 1;
  const color = l === "high" ? "bg-ok" : l === "medium" ? "bg-caution" : "bg-danger";
  return (
    <span className="inline-flex items-center gap-2 text-sm text-ink" title="Confidence in the evidence match, not a probability">
      <Gauge size={15} className="text-muted" aria-hidden />
      <span className="flex gap-0.5" aria-hidden>
        {[1, 2, 3].map((i) => <span key={i} className={cx("h-3 w-1.5 rounded-sm", i <= filled ? color : "bg-line")} />)}
      </span>
      <span>Confidence: <b className="font-semibold">{level}</b></span>
    </span>
  );
}

export function EvidenceStatusBadge({ status }: { status: string }) {
  const evidence = status.toLowerCase() === "evidence-based";
  return (
    <Pill
      className={evidence ? "bg-signal/15 text-signal ring-1 ring-signal/40" : "border border-dashed border-caution/60 text-caution"}
      icon={evidence ? <Eye size={13} aria-hidden /> : <FileSearch size={13} aria-hidden />}
    >
      {evidence ? "Evidence-based" : "Exploratory"}
    </Pill>
  );
}
