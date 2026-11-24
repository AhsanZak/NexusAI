import { authHeaders } from "../auth/session";

export interface OlistCounts {
  orders: number;
  customers: number;
  products: number;
  sellers: number;
  items: number;
  reviews: number;
  geolocation: number;
}

export interface OlistMonth {
  month: string;
  orders: number;
  revenue: number;
  freight: number;
}

export interface OlistStatus {
  status: string;
  orders: number;
}

export interface OlistCategory {
  category: string;
  items: number;
  revenue: number;
}

export interface OlistScore {
  score: number;
  reviews: number;
}

export interface OlistPayment {
  payment_type: string;
  payments: number;
  amount: number;
}

export interface OlistDashboard {
  attribution: string;
  source_url: string;
  licence: string;
  currency: string;
  counts: OlistCounts;
  monthly_sales: OlistMonth[];
  order_status: OlistStatus[];
  categories: OlistCategory[];
  review_scores: OlistScore[];
  review_summary: {
    reviews: number;
    average_score: number;
    with_comment: number;
  };
  delivery: {
    delivered: number;
    on_time: number;
    late: number;
    on_time_percent: number;
    average_days: number;
  };
  payments: OlistPayment[];
}

const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";

export async function loadOlistDashboard(): Promise<OlistDashboard> {
  const response = await fetch(`${apiBase}/api/v1/olist/dashboard`, { headers: authHeaders() });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    const detail = typeof body?.detail === "string" ? body.detail : "";
    throw new Error(detail || `Olist dashboard returned ${response.status}`);
  }
  return (await response.json()) as OlistDashboard;
}
