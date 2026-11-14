import type { ButtonHTMLAttributes, ReactNode } from "react";
import { AlertTriangle, CloudOff, Inbox, RotateCw, ShieldAlert } from "lucide-react";

export const cx = (...c: (string | false | null | undefined)[]) => c.filter(Boolean).join(" ");

/* ---------- Card ---------- */
export function Card({ children, className, tone, as: Tag = "section", id }:
  { children: ReactNode; className?: string; tone?: "default" | "danger" | "signal"; as?: "section" | "div" | "article"; id?: string }) {
  return (
    <Tag id={id} className={cx("scroll-mt-20",
      "rounded-card border bg-surface shadow-card",
      tone === "danger" ? "border-danger/50 shadow-danger" : tone === "signal" ? "border-signal/40 shadow-glow" : "border-line",
      className,
    )}>
      {children}
    </Tag>
  );
}

export function CardHeader({ eyebrow, title, right }: { eyebrow?: string; title: ReactNode; right?: ReactNode }) {
  return (
    <header className="flex items-start justify-between gap-4 border-b border-line/70 px-5 py-4">
      <div>
        {eyebrow && <p className="eyebrow mb-1">{eyebrow}</p>}
        <h3 className="text-h3 text-ink">{title}</h3>
      </div>
      {right}
    </header>
  );
}

/* ---------- Button ---------- */
type BtnVariant = "primary" | "secondary" | "ghost";
const BTN: Record<BtnVariant, string> = {
  primary: "bg-flare text-space hover:bg-flare/90 font-semibold",
  secondary: "border border-line bg-transparent text-ink hover:border-ink/40 hover:bg-raised",
  ghost: "text-muted hover:bg-raised hover:text-ink",
};
export function Button({ variant = "primary", icon, children, className, ...rest }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant; icon?: ReactNode }) {
  return (
    <button
      className={cx("inline-flex h-10 items-center gap-2 rounded-full px-5 text-base transition-colors disabled:opacity-50", BTN[variant], className)}
      {...rest}
    >
      {icon}
      {children}
    </button>
  );
}

/* ---------- Callout: blockers (danger) and flags (caution) ---------- */
export function Callout({ tone, title, items, children }:
  { tone: "danger" | "caution"; title: string; items?: string[]; children?: ReactNode }) {
  const Icon = tone === "danger" ? ShieldAlert : AlertTriangle;
  return (
    <div role="note" className={cx(
      "rounded-card border p-4",
      tone === "danger" ? "border-danger/50 bg-danger/10" : "border-caution/40 bg-caution/10",
    )}>
      <p className={cx("flex items-center gap-2 font-semibold", tone === "danger" ? "text-danger" : "text-caution")}>
        <Icon size={18} aria-hidden /> {title}
      </p>
      {items && items.length > 0 && (
        <ul className="mt-2 space-y-1.5 pl-7 text-ink/90">
          {items.map((t) => <li key={t} className="list-disc marker:text-faint">{t}</li>)}
        </ul>
      )}
      {children}
    </div>
  );
}

/* ---------- Loading / empty / error states ---------- */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cx("skeleton", className ?? "h-4 w-full")} />;
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-card border border-dashed border-line p-8 text-center">
      <Inbox className="text-faint" size={28} aria-hidden />
      <p className="font-semibold text-ink">{title}</p>
      {hint && <p className="max-w-sm text-sm text-muted">{hint}</p>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center justify-center gap-3 rounded-card border border-danger/40 bg-danger/5 p-8 text-center">
      <CloudOff className="text-danger" size={28} aria-hidden />
      <p className="font-semibold text-ink">Can't load this data</p>
      <p className="max-w-md text-sm text-muted">{message}</p>
      {onRetry && <Button variant="secondary" icon={<RotateCw size={16} />} onClick={onRetry}>Try again</Button>}
    </div>
  );
}

/** "Not available" — rule: never invent numbers (PRD Part D3). */
export function NotAvailable() {
  return <span className="italic text-faint">not available</span>;
}
