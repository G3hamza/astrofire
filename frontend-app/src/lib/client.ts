import { api } from "./api";
import type {
  CsvRow, DataQuality, GapCell, MapPoint, MaterialDetail, MaterialFamily, MaterialOverview, Missions,
  Overview, ScenarioRequest, ScenarioResult, Stats,
} from "./types";

/** Typed client: one function per endpoint the UI uses. Only /api/* (NFR8). */
const post = (body: unknown) => ({ method: "POST", body: JSON.stringify(body) });

export const client = {
  stats: () => api<Stats>("/api/stats"),
  overview: () => api<Overview>("/api/analytics/overview"),
  missions: () => api<Missions>("/api/missions"),
  materialFamilies: () => api<MaterialFamily[]>("/api/material-families"),
  materials: () => api<MaterialOverview[]>("/api/materials"),
  material: (id: string) => api<MaterialDetail>(`/api/materials/${encodeURIComponent(id)}`),
  scenario: (req: ScenarioRequest) => api<ScenarioResult>("/api/scenario", post(req)),
  gaps: () => api<GapCell[]>("/api/gaps"),
  map: (material?: string) => api<MapPoint[]>(`/api/map${material ? `?material=${encodeURIComponent(material)}` : ""}`),
  dataQuality: () => api<DataQuality>("/api/data-quality"),
  investigations: () => api<CsvRow[]>("/api/investigations"),
  droplets: () => api<CsvRow[]>("/api/droplets"),
  coolFlames: () => api<CsvRow[]>("/api/cool-flames"),
  gasFlames: () => api<CsvRow[]>("/api/gas-flames"),
  sessionLogs: () => api<CsvRow[]>("/api/session-logs"),
  experimentRows: (id: string) => api<{ total: number; records: Record<string, string | null>[] }>(`/api/experiments?investigation_id=${id}&limit=500`),
  smoke: (materialId?: string) => api<CsvRow[]>(`/api/smoke${materialId ? `?material_id=${encodeURIComponent(materialId)}` : ""}`),
  gasJets: () => api<CsvRow[]>("/api/gas-jets"),
  investigationProfiles: () => api<InvestigationProfile[]>("/api/investigations/profiles"),
  habitats: () => api<Record<string, Habitat>>("/api/habitats"),
  rank: (habitat: string, pillar?: string) => api<RankResult>(`/api/rank?habitat=${encodeURIComponent(habitat)}${pillar ? `&pillar=${pillar}` : ""}`),
  investigationsCompare: (ids: string[]) => api<InvestigationCompare>(`/api/investigations/compare?ids=${ids.map(encodeURIComponent).join(",")}`),
};

/* ---------- investigation profiles (/api/investigations/profiles) ---------- */
export type ProfileCondition = {
  factor: string; column: string; kind: "range" | "values"; unit: string; distinct: number; records_with_value: number;
  min?: number; max?: number; values?: { value: string; records: number }[];
};
export type KeywordHit = { sensor: string; evidence: string; basis?: string };
export type InvestigationProfile = {
  investigation_id: string; acronym: string; title: string; objective: string; hypothesis: string; approach: string;
  research_impacts: string; hardware: string; flight_program: string; project_type: string; start_date: string; end_date: string;
  doi: string; psi_url: string; pillar: string; pillar_secondary: string | null; relevance_tier: string; hardware_family: string;
  fuel_phase: string; study_type: string; partial_gravity_note: string | null; curation_basis: string; records: number;
  conditions: ProfileCondition[]; varied_factors: string[]; constant_factors: { factor: string; value: string | number; unit: string }[];
  not_recorded_factors: string[]; outcomes: { by_class: Record<string, number>; by_basis: Record<string, number> } | null;
  sensors: KeywordHit[]; measured_quantities: KeywordHit[]; publications_count: number;
  publications: { title: string; authors: string; doi: string }[];
  data_files: { files: number; total_gb: number; file_types: Record<string, number>; has_video: boolean; has_images: boolean } | null;
};
export type InvestigationCompare = {
  investigations: Partial<InvestigationProfile>[]; same: Record<string, boolean>;
  factors: { in_all: string[]; only_in: Record<string, string[]> };
  sensors: { in_all: string[]; only_in: Record<string, string[]> };
  measured_quantities: { in_all: string[]; only_in: Record<string, string[]> }; note: string;
};

export const PSI_PORTAL = "https://psi.nasa.gov/physci/repo/data/investigations";

/* ---------- habitat ranking (/api/rank) ---------- */
export type Habitat = { name: string; kind: string; gravity_g: number; o2_pct: number; pressure_kpa: number };
export type RankRow = {
  rank: number; investigation_id: string; acronym: string; title: string; pillar: string; pillar_secondary: string | null;
  relevance_tier: string; fuel_phase: string; hardware_family: string; psi_url: string; score: number;
  components: Record<"conditions" | "relevance" | "fuel" | "evidence", number>;
  condition_parts: Record<"oxygen" | "pressure" | "gravity", number>; reasons: string[];
};
export type RankResult = { habitat: Habitat & { key: string }; weights: Record<string, number>; method: string; caveat: string; ranked: RankRow[] };
