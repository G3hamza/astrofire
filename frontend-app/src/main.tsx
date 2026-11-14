import { lazy, StrictMode, Suspense, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { EmptyState, Skeleton } from "./components/ui";
import GapsPage from "./pages/GapsPage";
import HomePage from "./pages/HomePage";
import ScenarioPage from "./pages/ScenarioPage";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "./index.css";

// Heavier, less-visited pages load on demand (Recharts lives only in the charts chunk).
const ChartsPage = lazy(() => import("./pages/ChartsPage"));
const AboutPage = lazy(() => import("./pages/AboutPage"));
const ComparePage = lazy(() => import("./pages/ComparePage"));
const ExperimentsPage = lazy(() => import("./pages/ExperimentsPage"));
const InvestigationsPage = lazy(() => import("./pages/InvestigationsPage"));
const ApplicationsPage = lazy(() => import("./pages/ApplicationsPage"));
const AskPage = lazy(() => import("./pages/AskPage"));
const RankPage = lazy(() => import("./pages/RankPage"));
const DataQualityPage = lazy(() => import("./pages/DataQualityPage"));
const StylePage = lazy(() => import("./pages/StylePage"));
const MaterialsList = lazy(() => import("./pages/MaterialsPage").then((m) => ({ default: m.MaterialsList })));
const MaterialDetail = lazy(() => import("./pages/MaterialsPage").then((m) => ({ default: m.MaterialDetail })));

const TITLES: [RegExp, (m: RegExpMatchArray) => string][] = [
  [/^\/$/, () => "Home"], [/^\/scenario/, () => "Scenario check"], [/^\/compare/, () => "Compare scenarios"], [/^\/gaps/, () => "Gaps map"],
  [/^\/charts/, () => "Evidence charts"], [/^\/experiments/, () => "NASA experiments"], [/^\/investigations/, () => "Investigations"], [/^\/rank/, () => "Habitat ranking"], [/^\/ask/, () => "Ask"], [/^\/applications/, () => "Data and applications"],
  [/^\/materials\/(.+)/, (m) => `Material ${decodeURIComponent(m[1])}`], [/^\/materials/, () => "Materials"],
  [/^\/data/, () => "Data quality"], [/^\/about/, () => "About"], [/^\/style/, () => "Design system"],
];

function RouteEffects() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    let name = "Page not found";
    for (const [re, fn] of TITLES) { const m = pathname.match(re); if (m) { name = fn(m); break; } }
    document.title = `${name} · StarryNight`;
    if (!hash) window.scrollTo(0, 0);
  }, [pathname, hash]);
  return null;
}

function NotFound() {
  return (
    <div className="mx-auto max-w-xl space-y-4 pt-10">
      <EmptyState title="This page doesn't exist" hint="The link may be old. Every StarryNight screen is in the top menu." />
      <p className="text-center"><Link to="/">Back to Home</Link></p>
    </div>
  );
}

function PageLoading() {
  return <div className="space-y-4" aria-label="Loading"><Skeleton className="h-10 w-1/2" /><Skeleton className="h-80 rounded-card" /></div>;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <RouteEffects />
      <AppShell>
        <Suspense fallback={<PageLoading />}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/scenario" element={<ScenarioPage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/gaps" element={<GapsPage />} />
            <Route path="/charts" element={<ChartsPage />} />
            <Route path="/experiments" element={<ExperimentsPage />} />
            <Route path="/investigations" element={<InvestigationsPage />} />
            <Route path="/rank" element={<RankPage />} />
            <Route path="/ask" element={<AskPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/materials" element={<MaterialsList />} />
            <Route path="/materials/:id" element={<MaterialDetail />} />
            <Route path="/data" element={<DataQualityPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/style" element={<StylePage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </AppShell>
    </BrowserRouter>
  </StrictMode>,
);
