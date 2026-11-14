import { ChevronDown, Menu, X } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { AskPanel } from "./AskPanel";
import { cx } from "./ui";

/* StarryNight shell: logo, pill navigation (primary routes + "More"), a live evidence-base readout, footer sitemap. */

const PRIMARY = [
  { to: "/", label: "Home", end: true },
  { to: "/scenario", label: "Scenario" },
  { to: "/ask", label: "Ask AI" },
  { to: "/rank", label: "Rank" },
  { to: "/gaps", label: "Gaps" },
  { to: "/investigations", label: "Investigations" },
];
const MORE = [
  { to: "/compare", label: "Compare scenarios", note: "2-4 side by side" },
  { to: "/charts", label: "Evidence charts", note: "Flammability map" },
  { to: "/experiments", label: "NASA experiments", note: "All 24 investigations" },
  { to: "/materials", label: "Materials", note: "Named vs unknown" },
  { to: "/applications", label: "Apply", note: "Data, equipment, Earth" },
  { to: "/data", label: "Data quality", note: "Observed vs inferred" },
  { to: "/about", label: "About", note: "Judging criteria, AI use" },
];

export function Logo({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden>
      <rect x="0.5" y="0.5" width="31" height="31" rx="9" fill="rgb(var(--surface))" stroke="rgb(var(--line))" />
      <path d="M16 5.5c.9 5.4 3.6 8.6 10.5 10.5-6.9 1.9-9.6 5.1-10.5 10.5-.9-5.4-3.6-8.6-10.5-10.5C12.4 14.1 15.1 10.9 16 5.5Z" fill="rgb(var(--signal))" />
      <circle cx="16" cy="16" r="2.2" fill="rgb(var(--flare))" />
    </svg>
  );
}

const pill = (active: boolean) => cx(
  "inline-flex h-9 items-center gap-1.5 whitespace-nowrap rounded-full border px-3.5 text-sm font-medium no-underline transition-colors hover:no-underline",
  active ? "border-ink/25 bg-ink/[0.07] text-ink" : "border-transparent text-muted hover:border-line hover:text-ink",
);

function MoreMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { pathname } = useLocation();
  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const click = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    const key = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", click); document.addEventListener("keydown", key);
    return () => { document.removeEventListener("mousedown", click); document.removeEventListener("keydown", key); };
  }, [open]);
  const active = MORE.some((m) => pathname.startsWith(m.to));
  return (
    <div ref={ref} className="relative">
      <button type="button" aria-expanded={open} aria-haspopup="true" onClick={() => setOpen((o) => !o)} className={pill(active || open)}>
        More <ChevronDown size={14} className={cx("transition-transform", open && "rotate-180")} aria-hidden />
      </button>
      {open && (
        <div role="menu" className="absolute right-0 top-11 z-50 w-72 rounded-card border border-line bg-surface p-1.5 shadow-card">
          {MORE.map((m) => (
            <NavLink key={m.to} to={m.to} role="menuitem"
              className={({ isActive }) => cx("flex items-baseline justify-between gap-3 rounded-lg px-3 py-2 no-underline hover:no-underline",
                isActive ? "bg-raised text-ink" : "text-ink/90 hover:bg-raised")}>
              <span className="text-sm font-medium">{m.label}</span>
              <span className="font-mono text-[0.7rem] text-faint">{m.note}</span>
            </NavLink>
          ))}
        </div>
      )}
    </div>
  );
}

function MobileNav() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => setOpen(false), [pathname]);
  return (
    <div className="lg:hidden">
      <button type="button" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} onClick={() => setOpen((o) => !o)}
        className="grid h-9 w-9 place-items-center rounded-full border border-line text-ink">
        {open ? <X size={16} aria-hidden /> : <Menu size={16} aria-hidden />}
      </button>
      {open && (
        <nav aria-label="Mobile" className="absolute inset-x-0 top-16 z-50 border-b border-line bg-space px-4 pb-4">
          <ul className="grid grid-cols-2 gap-1 pt-2">
            {[...PRIMARY, ...MORE].map((n) => (
              <li key={n.to}><NavLink to={n.to} end={"end" in n} className={({ isActive }) => cx("block rounded-lg px-3 py-2 text-sm no-underline hover:no-underline", isActive ? "bg-raised text-ink" : "text-muted")}>{n.label}</NavLink></li>
            ))}
          </ul>
        </nav>
      )}
    </div>
  );
}

const FOOTER: { title: string; links: { label: string; to?: string; href?: string }[] }[] = [
  { title: "Explore", links: [{ label: "Scenario check", to: "/scenario" }, { label: "Compare scenarios", to: "/compare" }, { label: "Gaps map", to: "/gaps" }, { label: "Evidence charts", to: "/charts" }] },
  { title: "Research", links: [{ label: "Habitat ranking", to: "/rank" }, { label: "Investigations", to: "/investigations" }, { label: "NASA experiments", to: "/experiments" }, { label: "Materials", to: "/materials" }] },
  { title: "Use", links: [{ label: "Ask the analyst", to: "/ask" }, { label: "Data and applications", to: "/applications" }, { label: "Data quality", to: "/data" }, { label: "API reference", href: "/docs" }] },
  { title: "Project", links: [{ label: "About and AI use", to: "/about" }, { label: "Source code", href: "https://github.com/G3hamza/astrofire" }, { label: "Handbook (PDF)", href: "https://github.com/G3hamza/astrofire/blob/main/docs/StarryNight_Handbook.pdf" }, { label: "Lite version", href: "/lite/" }] },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-signal focus:px-3 focus:py-2 focus:text-space">
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b border-line/60 bg-space/90 backdrop-blur-md">
        <div className="relative mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5 text-ink no-underline hover:no-underline" aria-label="StarryNight home">
            <Logo className="h-8 w-8" />
            <span className="text-[1.05rem] font-semibold tracking-tight">StarryNight</span>
          </Link>
          <nav aria-label="Main" className="ml-4 hidden items-center gap-1 lg:flex">
            {PRIMARY.map(({ to, label, end }) => (
              <NavLink key={to} to={to} end={end} className={({ isActive }) => pill(isActive)}>{label}</NavLink>
            ))}
            <MoreMenu />
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <span className="hidden h-9 items-center gap-2 whitespace-nowrap rounded-full border border-line px-3.5 font-mono text-[0.72rem] text-muted xl:inline-flex"
              title="Every answer is built from this NASA evidence base">
              Evidence base <span className="h-1.5 w-1.5 rounded-full bg-ok" aria-hidden /> <span className="text-ink">NASA PSI · 24 investigations</span>
            </span>
            <Link to="/scenario" className="hidden h-9 items-center rounded-full bg-flare px-4 text-sm font-semibold text-space no-underline hover:bg-flare/90 hover:no-underline sm:inline-flex">
              Check a scenario
            </Link>
            <MobileNav />
          </div>
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">{children}</main>
      <AskPanel />

      <footer className="mt-16 border-t border-line/60">
        <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div className="space-y-3">
            <div className="flex items-center gap-2.5"><Logo className="h-7 w-7" /><span className="font-semibold">StarryNight</span></div>
            <p className="max-w-xs text-sm text-muted">Space fire safety intelligence, built only on NASA's Physical Sciences Informatics combustion data.</p>
            <p className="font-mono text-[0.72rem] uppercase tracking-[0.18em] text-faint">Better research · Better understanding · A safer future beyond Earth</p>
          </div>
          {FOOTER.map((col) => (
            <div key={col.title}>
              <p className="mb-3 text-sm font-semibold text-ink">{col.title}</p>
              <ul className="space-y-2 text-sm">
                {col.links.map((l) => (
                  <li key={l.label}>{l.to
                    ? <Link to={l.to} className="text-muted no-underline hover:text-ink hover:no-underline">{l.label}</Link>
                    : <a href={l.href} className="text-muted no-underline hover:text-ink hover:no-underline" {...(l.href?.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}>{l.label}</a>}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-line/40">
          <p className="mx-auto max-w-7xl px-4 py-5 text-xs text-faint sm:px-6">
            NASA Space Apps Cairo 2026 · Flame in Freefall · Team Starry Night · Data and imagery: NASA (public domain). StarryNight is not endorsed by NASA.
          </p>
        </div>
      </footer>
    </div>
  );
}
