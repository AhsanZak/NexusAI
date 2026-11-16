export interface WorldBankIndicator {
  code: string;
  name: string;
}

export interface WorldBankPoint {
  year: number;
  value: number;
}

export interface WorldBankSeries {
  indicator_code: string;
  indicator_name: string;
  country_code: string;
  country_name: string;
  points: WorldBankPoint[];
}

export interface WorldBankDocument {
  id: string;
  title: string;
  doc_type: string | null;
  document_date: string | null;
  abstract: string | null;
  url: string | null;
  pdf_url: string | null;
}

export interface WorldBankDashboard {
  attribution: string;
  indicator_source: string;
  document_source: string;
  retrieved_at: string | null;
  observation_count: number;
  document_count: number;
  indicators: WorldBankIndicator[];
  series: WorldBankSeries[];
  documents: WorldBankDocument[];
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

export async function loadWorldBankDashboard(): Promise<WorldBankDashboard> {
  const response = await fetch(`${apiBase}/api/v1/worldbank/dashboard`);
  if (!response.ok) {
    throw new Error(`World Bank dashboard returned ${response.status}`);
  }
  return (await response.json()) as WorldBankDashboard;
}
