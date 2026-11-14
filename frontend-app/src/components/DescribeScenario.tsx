import { AlertTriangle, Check, CornerDownLeft, MessageSquareText, Sparkles } from "lucide-react";
import { useState, type FormEvent } from "react";
import { api } from "../lib/api";
import type { ScenarioRequest } from "../lib/types";
import { Card, cx } from "./ui";

export type ParseResult = {
  scenario: ScenarioRequest & { mission: ScenarioRequest["mission"] };
  understood: { field: string; value: string | number; text: string }[];
  defaulted: { field: string; value: string | number; reason: string }[];
  warnings: string[];
};

const LABEL: Record<string, string> = {
  material: "Material", mission: "Mission", o2_pct: "Oxygen %", pressure_kpa: "Pressure kPa", gravity_g: "Gravity g", flow_cm_s: "Air flow cm/s",
};
const EXAMPLES = [
  "Nomex on Mars at 34% oxygen and 8.2 psi",
  "Acrylic window in a lunar habitat, 30% O2, 0.5 atm, 2 cm/s air flow",
  "Kevlar seat cover in microgravity at 26% oxygen, 70 kPa",
];

/** Free-text scenario entry. Rule-based for now (POST /api/scenario/parse); the team chatbot will plug into the same contract. */
export function DescribeScenario({ onParsed, compact }: { onParsed: (r: ParseResult) => void; compact?: boolean }) {
  const [text, setText] = useState("");
  const [res, setRes] = useState<ParseResult | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async (t: string) => {
    if (t.trim().length < 3) return;
    setBusy(true); setErr(null);
    try {
      const r = await api<ParseResult>("/api/scenario/parse", { method: "POST", body: JSON.stringify({ text: t }) });
      setRes(r); onParsed(r);
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };
  const submit = (e: FormEvent) => { e.preventDefault(); run(text); };

  return (
    <Card className={compact ? "border-0 bg-transparent p-0 shadow-none" : "p-5"}>
      <form onSubmit={submit} className="space-y-3">
        <label htmlFor="describe" className="flex items-center gap-2 text-h3">
          <MessageSquareText size={18} className="text-signal" aria-hidden /> Describe your scenario in your own words
        </label>
        <div className="relative">
          <textarea id="describe" rows={2} value={text} onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); run(text); } }}
            placeholder="e.g. Nomex on Mars at 34% oxygen and 8.2 psi"
            className="w-full resize-none rounded-lg border border-line bg-raised p-3 pr-28 text-ink placeholder:text-faint focus:border-signal" />
          <button type="submit" disabled={busy} className="absolute bottom-3 right-2 inline-flex h-9 items-center gap-2 rounded-lg bg-signal px-3 text-sm font-semibold text-space hover:bg-signal/90 disabled:opacity-60">
            Check <CornerDownLeft size={14} aria-hidden />
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-faint">Try:</span>
          {EXAMPLES.map((x) => (
            <button key={x} type="button" onClick={() => { setText(x); run(x); }}
              className="rounded-full border border-line bg-raised px-3 py-1 text-muted hover:text-ink">{x}</button>
          ))}
        </div>
        <p className="flex items-center gap-1.5 text-[12px] text-faint"><Sparkles size={12} aria-hidden />
          Simple word matching for now (no AI). The team's chatbot will replace it. You can always adjust the fields below.</p>
      </form>

      {err && <p role="alert" className="mt-3 text-sm text-danger">{err}</p>}
      {res && (
        <div className="mt-4 space-y-2 border-t border-line/60 pt-4 text-sm" aria-live="polite">
          {res.understood.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="eyebrow">Understood</span>
              {res.understood.map((u) => (
                <span key={u.field} title={`from "${u.text}"`} className="inline-flex items-center gap-1 rounded-full bg-ok/15 px-2.5 py-0.5 text-ok ring-1 ring-ok/40">
                  <Check size={12} aria-hidden /> {LABEL[u.field] ?? u.field}: <b>{String(u.value)}</b>
                </span>
              ))}
            </div>
          )}
          {res.defaulted.length > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="eyebrow">Filled in</span>
              {res.defaulted.map((d) => (
                <span key={d.field} title={d.reason} className={cx("inline-flex items-center gap-1 rounded-full border border-dashed border-line px-2.5 py-0.5 text-muted")}>
                  {LABEL[d.field] ?? d.field}: {String(d.value)} <span className="text-faint">({d.reason})</span>
                </span>
              ))}
            </div>
          )}
          {res.warnings.map((w) => (
            <p key={w} className="flex items-start gap-2 text-caution"><AlertTriangle size={14} className="mt-0.5 shrink-0" aria-hidden /> {w}</p>
          ))}
        </div>
      )}
    </Card>
  );
}
