import { Ban, Flame, Scale, ShieldAlert } from "lucide-react";
import { verdictTone, type VerdictTone } from "../lib/domain";
import { ConfidenceBadge, EvidenceStatusBadge } from "./badges";
import { cx } from "./ui";

const TONE: Record<VerdictTone, { box: string; text: string; Icon: typeof Flame; eyebrow: string }> = {
  burn: { box: "border-burn/50 bg-burn/10", text: "text-burn", Icon: Flame, eyebrow: "What NASA tests show" },
  out: { box: "border-out/50 bg-out/10", text: "text-out", Icon: Ban, eyebrow: "What NASA tests show" },
  caution: { box: "border-caution/50 bg-caution/10", text: "text-caution", Icon: Scale, eyebrow: "What NASA tests show" },
  danger: { box: "border-danger/60 bg-danger/10 shadow-danger", text: "text-danger", Icon: ShieldAlert, eyebrow: "NASA has no tests here" },
};

/** The verdict string is shown verbatim from the API (NFR1). */
export function VerdictBanner({ verdict, confidence, evidenceStatus, size = "lg" }:
  { verdict: string; confidence: string; evidenceStatus: string; size?: "lg" | "sm" }) {
  const t = TONE[verdictTone(verdict)];
  const sm = size === "sm";
  return (
    <div role="status" className={cx("flex flex-col gap-4 rounded-card border", sm ? "p-4" : "p-6 sm:flex-row sm:items-center", t.box)}>
      <div className="flex flex-1 items-center gap-4">
        <t.Icon size={sm ? 30 : 44} className={cx("shrink-0", t.text)} aria-hidden strokeWidth={1.75} />
        <div className="flex-1">
          <p className="eyebrow mb-1">{t.eyebrow}</p>
          <p className={cx(sm ? "text-h3" : "text-h2", t.text)}>{verdict}</p>
        </div>
      </div>
      <div className={cx("flex gap-2", sm ? "flex-wrap items-center gap-4" : "flex-col items-start sm:items-end")}>
        <EvidenceStatusBadge status={evidenceStatus} />
        <ConfidenceBadge level={confidence} />
      </div>
    </div>
  );
}
