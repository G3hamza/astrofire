import { ChartScatter, Wrench, MessageSquareText, Database, GitCompare, FlaskConical, Flame, Grid3x3, ShieldCheck, Home, Layers, ListOrdered, Palette, Rocket } from "lucide-react";
import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { AskPanel } from "./AskPanel";
import { cx } from "./ui";

const NAV = [
  { to: "/", label: "Home", Icon: Home, end: true },
  { to: "/scenario", label: "Scenario", Icon: Rocket },
  { to: "/compare", label: "Compare", Icon: GitCompare },
  { to: "/gaps", label: "Gaps", Icon: Grid3x3 },
  { to: "/charts", label: "Charts", Icon: ChartScatter },
  { to: "/ask", label: "Ask", Icon: MessageSquareText },
  { to: "/rank", label: "Rank", Icon: ListOrdered },
  { to: "/investigations", label: "Investigations", Icon: Layers },
  { to: "/experiments", label: "Experiments", Icon: Database },
  { to: "/materials", label: "Materials", Icon: FlaskConical },
  { to: "/applications", label: "Apply", Icon: Wrench },
  { to: "/data", label: "Quality", Icon: ShieldCheck },
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-signal focus:px-3 focus:py-2 focus:text-space">
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b border-line/80 bg-space/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-3 px-4 sm:gap-6 sm:px-6">
          <NavLink to="/" className="flex items-center gap-2 text-ink no-underline hover:no-underline" aria-label="AstroFire home">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-burn/15 ring-1 ring-burn/40">
              <Flame size={18} className="text-burn" aria-hidden />
            </span>
            <span className="hidden text-lg font-bold tracking-tight min-[420px]:inline">Astro<span className="text-burn">Fire</span></span>
          </NavLink>
          <nav aria-label="Main" className="-mx-1 flex min-w-0 items-center gap-0.5 overflow-x-auto px-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {NAV.map(({ to, label, Icon, end }) => (
              <NavLink key={to} to={to} end={end}
                className={({ isActive }) => cx(
                  "flex h-9 items-center gap-2 whitespace-nowrap rounded-lg px-2.5 text-sm font-medium no-underline transition-colors hover:no-underline",
                  isActive ? "bg-signal/15 text-signal" : "text-muted hover:bg-raised hover:text-ink",
                )}>
                <Icon size={16} aria-hidden />
                <span className="hidden lg:inline">{label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <NavLink to="/style" title="Design system"
              className={({ isActive }) => cx("hidden h-9 w-9 place-items-center rounded-lg sm:grid", isActive ? "text-signal" : "text-faint hover:text-ink")}>
              <Palette size={16} aria-label="Design system" />
            </NavLink>
            <span className="hidden items-center gap-2 whitespace-nowrap font-mono text-label uppercase text-muted 2xl:flex">
              <span className="h-2 w-2 animate-pulseDot rounded-full bg-ok" aria-hidden /> NASA PSI data
            </span>
          </div>
        </div>
      </header>
      <main id="main" className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6">{children}</main>
      <AskPanel />
      <footer className="border-t border-line/60 py-5 text-center text-sm text-faint">
        AstroFire · NASA Space Apps Cairo 2026 · Flame in Freefall · Team Starry Night ·{" "}
        <a href="/lite/">Lite version</a>
      </footer>
    </div>
  );
}
