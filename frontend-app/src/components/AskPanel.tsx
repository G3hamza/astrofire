import { MessageSquareText, X } from "lucide-react";
import { lazy, Suspense, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

// The chat loads only when the panel is first opened (keeps the first page load small).
const AskChat = lazy(() => import("../pages/AskPage").then((m) => ({ default: m.AskChat })));

/** Floating "Ask AI" button on every page (except /ask) that opens the evidence-grounded chat in a side panel. */
export function AskPanel() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);   // keep the conversation when the panel is closed and reopened
  useEffect(() => { if (open) setMounted(true); }, [open]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  if (pathname.startsWith("/ask")) return null;

  return (
    <>
      {!open && (
        <button type="button" onClick={() => setOpen(true)} aria-label="Ask StarryNight's AI analyst"
          className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-full border border-signal/50 bg-surface px-4 py-3 font-semibold text-ink shadow-card hover:border-signal">
          <MessageSquareText size={18} className="text-signal" aria-hidden /> Ask AI
        </button>
      )}
      <aside aria-label="StarryNight AI analyst" aria-hidden={!open}
        className={`fixed inset-y-0 right-0 z-50 w-full max-w-[480px] flex-col border-l border-line bg-space shadow-card ${open ? "flex" : "hidden"}`}>
        <header className="flex items-center gap-3 border-b border-line px-4 py-3">
          <MessageSquareText size={18} className="text-signal" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-ink">Ask NASA's fire data</p>
            <p className="text-xs text-muted">Answers built from NASA PSI records, every claim cited. Click [E#] to see the source.</p>
          </div>
          <button type="button" onClick={() => setOpen(false)} aria-label="Close the AI panel" className="rounded p-1 text-muted hover:bg-raised hover:text-ink">
            <X size={18} aria-hidden />
          </button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4">
          {mounted && <Suspense fallback={<p className="text-sm text-muted">Loading the analyst…</p>}><AskChat compact /></Suspense>}
        </div>
      </aside>
    </>
  );
}
