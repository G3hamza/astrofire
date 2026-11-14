import { useEffect, useRef, useState } from "react";
import { Button, Card, CardHeader, cx, ErrorState } from "../components/ui";
import { useSearchParams } from "react-router-dom";
import { api } from "../lib/api";

/* Basic, functional UI on purpose: all logic lives in POST /api/ask so a later redesign keeps it. */

type Evidence = { id: string; kind: string; text: string; acronym?: string; investigation_id?: string; source_file?: string;
  source_row?: number; psi_url?: string; url?: string; title?: string; level?: string };
type AskResult = { answer: string; findings: string[]; interpretation: string[]; limits: string[]; followups: string[];
  tools_used: string[]; mode: "ai" | "template"; model: string | null; intent: string; evidence: Evidence[];
  insufficient_evidence: boolean; latency_ms: number };
type Turn = { q: string; r?: AskResult; error?: string };
type Status = { ai_enabled: boolean; provider: string | null; model: string | null; retrieval: string; knowledge_base_chunks: number };

const HABITATS = [["", "No habitat"], ["iss", "ISS"], ["spacecraft", "Spacecraft"], ["moon", "Moon base"], ["rover", "Lunar rover"], ["mars", "Mars base"]];
const STARTERS = ["Which investigations matter most for a Moon base?", "Would Nomex burn at 30% oxygen and 71 kPa on the Moon?",
  "How do SAME and SAME-R differ?", "What does this research mean for next-generation smoke detectors?",
  "What data could I use to train a flammability model?", "What has never been tested for a Moon base?"];

function Cited({ text, ev, onPick }: { text: string; ev: Map<string, Evidence>; onPick: (e: Evidence) => void }) {
  const parts = text.split(/(\[E\d+\])/g);
  return <>{parts.map((p, i) => {
    const m = p.match(/^\[(E\d+)\]$/);
    const e = m ? ev.get(m[1]) : undefined;
    return e ? <button key={i} onClick={() => onPick(e)} title={e.title ?? e.kind}
      className="mx-0.5 rounded border border-signal/50 px-1 font-mono text-xs text-signal hover:bg-signal/10">{m![1]}</button>
      : <span key={i}>{p}</span>;
  })}</>;
}

function Answer({ r, onAsk }: { r: AskResult; onAsk: (q: string) => void }) {
  const ev = new Map(r.evidence.map((e) => [e.id, e]));
  const [pick, setPick] = useState<Evidence | null>(null);
  const Section = ({ title, items, tone }: { title: string; items: string[]; tone?: string }) => items.length ? (
    <div><p className={cx("eyebrow mb-1", tone)}>{title}</p>
      <ul className="list-disc space-y-1 pl-5">{items.map((x, i) => <li key={i}><Cited text={x} ev={ev} onPick={setPick} /></li>)}</ul></div>) : null;
  return (
    <div className="space-y-3 text-sm">
      <p className={cx("text-base", r.insufficient_evidence && "text-caution")}><Cited text={r.answer} ev={ev} onPick={setPick} /></p>
      <Section title="NASA findings" items={r.findings} />
      <Section title="StarryNight interpretation" items={r.interpretation} tone="text-signal" />
      <Section title="Limits and gaps" items={r.limits} tone="text-caution" />
      {pick && (
        <div className="rounded border border-signal/40 bg-raised p-3">
          <p className="eyebrow">{pick.id} · {pick.kind}{pick.level ? ` · ${pick.level}` : ""}{pick.acronym ? ` · ${pick.acronym}` : ""}</p>
          <p className="mt-1">{pick.text}</p>
          <p className="mt-1 text-xs text-muted">{pick.source_file}{pick.source_row ? ` · row ${pick.source_row}` : ""}</p>
          {(pick.psi_url || pick.url) && <a href={pick.psi_url ?? pick.url} target="_blank" rel="noreferrer" className="text-xs">Open source</a>}
        </div>)}
      <div className="flex flex-wrap gap-2">{r.followups.map((f) => <Button key={f} variant="secondary" onClick={() => onAsk(f)}>{f}</Button>)}</div>
      <p className="text-xs text-muted">{r.mode === "ai" ? `Written by ${r.model} from the evidence` : "Template answer from NASA records (not AI-written)"} ·
        intent {r.intent} · tools {r.tools_used.join(", ") || "none"} · {r.evidence.length} evidence items · {r.latency_ms} ms</p>
    </div>
  );
}

/** The chat itself: used full-size on /ask and compact in the "Ask AI" side panel on every page. */
export function AskChat({ compact = false, initialQuestion }: { compact?: boolean; initialQuestion?: string | null }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [q, setQ] = useState("");
  const [habitat, setHabitat] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<Status | null>(null);
  const end = useRef<HTMLDivElement>(null);
  const asked = useRef(false);
  useEffect(() => { api<Status>("/api/ask/status").then(setStatus).catch(() => setStatus(null)); }, []);
  useEffect(() => { if (turns.length) end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [turns]);

  const ask = async (question: string) => {
    const text = question.trim();
    if (!text || busy) return;
    const history = turns.filter((t) => t.r).slice(-3).flatMap((t) => [{ role: "user", content: t.q }, { role: "assistant", content: t.r!.answer }]);
    setTurns((t) => [...t, { q: text }]); setQ(""); setBusy(true);
    try {
      const r = await api<AskResult>("/api/ask", { method: "POST", body: JSON.stringify({ question: text, habitat: habitat || null, history }) });
      setTurns((t) => t.map((x, i) => i === t.length - 1 ? { ...x, r } : x));
    } catch (e) {
      setTurns((t) => t.map((x, i) => i === t.length - 1 ? { ...x, error: (e as Error).message } : x));
    } finally { setBusy(false); }
  };
  useEffect(() => {  // question handed over from the Home page box (/ask?q=...)
    if (initialQuestion && !asked.current) { asked.current = true; ask(initialQuestion); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  return (
    <div className="space-y-4">
      {status && <p className="text-xs text-muted">{status.ai_enabled ? `AI: ${status.provider} / ${status.model}` : "AI off: template answers (no API key)"} ·
        retrieval {status.retrieval} over {status.knowledge_base_chunks} PSI passages</p>}
      {turns.length === 0 && <div className="flex flex-wrap gap-2">{(compact ? STARTERS.slice(0, 4) : STARTERS).map((s) =>
        <Button key={s} variant="secondary" className={compact ? "text-xs" : undefined} onClick={() => ask(s)}>{s}</Button>)}</div>}
      <div className="space-y-4">
        {turns.map((t, i) => (
          <Card key={i}>
            <CardHeader eyebrow="Question" title={t.q} />
            <div className={compact ? "px-4 py-3" : "px-5 py-4"}>
              {t.r ? <Answer r={t.r} onAsk={ask} /> : t.error ? <ErrorState message={t.error} onRetry={() => ask(t.q)} />
                : <p className="text-sm text-muted" aria-live="polite">Retrieving NASA evidence and checking it…</p>}
            </div>
          </Card>))}
        <div ref={end} />
      </div>
      <form className="sticky bottom-0 flex flex-wrap gap-2 rounded-card border border-line bg-surface p-3 shadow-card" onSubmit={(e) => { e.preventDefault(); ask(q); }}>
        <select aria-label="Habitat" className="rounded border border-line bg-raised px-2 py-1 text-sm" value={habitat} onChange={(e) => setHabitat(e.target.value)}>
          {HABITATS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <input aria-label="Question" className="min-w-0 flex-1 rounded border border-line bg-raised px-3 py-2 text-sm" maxLength={1000}
          placeholder="Ask about NASA fire tests, a habitat, a material…" value={q} onChange={(e) => setQ(e.target.value)} />
        <Button type="submit" disabled={busy || !q.trim()}>{busy ? "Working…" : "Ask"}</Button>
      </form>
    </div>
  );
}

export default function AskPage() {
  const [sp] = useSearchParams();
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <p className="eyebrow">Evidence-grounded analyst</p>
        <h1 className="text-h1 text-ink">Ask NASA's fire data</h1>
        <p className="max-w-3xl text-muted">Every answer is built from NASA PSI records through StarryNight's engines. Click an [E#] citation to see the record,
          file and row. Verdicts come from the rule engine; the AI only explains them.</p>
      </header>
      <AskChat initialQuestion={sp.get("q")} />
    </div>
  );
}
