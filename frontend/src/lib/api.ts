/** API client for the PakMind unified backend. */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Core response types ───

export interface GuideResponse {
  module: string;
  answer: string;
  requirements: string[];
  steps: string[];
  fee: string | null;
  processing_time: string | null;
  application_method: string | null;
  application_url: string | null;
  contact_info: Record<string, unknown> | null;
  eligibility: string | null;
  confidence: "high" | "medium" | "low";
  source_type?: string;
  sources: { title: string | null; url: string | null; source_name: string | null }[];
  warnings: string[];
  voice_answer?: string;
}

export interface WatchResponse {
  module: string;
  answer: string;
  updates: {
    title: string | null;
    category: string | null;
    province: string | null;
    department: string | null;
    organization: string | null;
    summary: string | null;
    importance: string | null;
    published_date: string | null;
  }[];
  sources: { title: string | null; url: string | null; source_name: string | null }[];
  what_changed: string | null;
  who_affected: string | null;
  effective_date: string | null;
  confidence: "high" | "medium" | "low";
  warnings: string[];
  web_sources?: { title: string; url: string }[];
  model?: string;
}

export interface ScholarResponse {
  database_matches: {
    title: string;
    organization: string;
    eligible: boolean | string;
    reasoning: string;
    deadline: string | null;
    application_url: string | null;
    type?: string;
    province?: string;
    degree_level?: string;
    amount?: string;
  }[];
  web_matches: {
    title: string;
    url: string;
    snippet: string;
    relevant: boolean | string;
    reasoning: string;
  }[];
  answer_summary: string;
  web_summary: string;
  detected_language?: string;
  error?: boolean;
  message?: string;
}

export interface GuideSearchResult {
  results: {
    id: string;
    name: string;
    description: string | null;
    province: string | null;
    city: string | null;
    fee: string | null;
    processing_time: string | null;
    status: string | null;
  }[];
}

export interface WatchSearchResult {
  results: {
    id: string;
    title: string;
    category: string | null;
    province: string | null;
    department: string | null;
    summary: string | null;
    importance: string | null;
    published_date: string | null;
  }[];
}

export interface HotTopic {
  topic: string;
  query?: string | null;
  answer: string | null;
  what_changed: string | null;
  who_affected: string | null;
  effective_date: string | null;
  confidence: "high" | "medium" | "low";
  generated_at: string | null;
  model?: string | null;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface Opportunity {
  id: string;
  title: string;
  organization: string;
  type: string | null;
  amount: string | null;
  deadline: string | null;
  province: string | null;
  degree_level: string | null;
  eligibility_criteria: string | null;
  application_url: string | null;
  status: string | null;
}

// ─── Module name types ───

export type ModuleName = "guide" | "watch" | "scholar";

export interface SmartResult {
  module: ModuleName;
  data: GuideResponse | WatchResponse | ScholarResponse;
}

// ─── Fetch helpers ───

async function fetchJson<T>(url: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API error (${res.status}): ${text}`);
  }
  return res.json();
}

async function fetchGet<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API error (${res.status}): ${text}`);
  }
  return res.json();
}

// ─── PakGuide API ───

export async function queryGuide(question: string): Promise<GuideResponse> {
  return fetchJson<GuideResponse>(
    `${API_BASE}/api/guide/query`,
    { query: question }
  );
}

export async function searchGuide(query: string): Promise<GuideSearchResult> {
  return fetchJson<GuideSearchResult>(
    `${API_BASE}/api/guide/search`,
    { query }
  );
}

export async function submitFeedback(
  query: string,
  rating: number,
  comment?: string,
  responseSnapshot?: Record<string, unknown>
): Promise<Record<string, unknown>> {
  return fetchJson<Record<string, unknown>>(
    `${API_BASE}/api/feedback/submit`,
    { query, rating, comment, response_snapshot: responseSnapshot }
  );
}

export async function getFeedbackStats(): Promise<Record<string, unknown>> {
  return fetchGet<Record<string, unknown>>(`${API_BASE}/api/feedback/stats`);
}

export async function generateChecklistPdf(data: Record<string, unknown>): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/feedback/checklist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`PDF generation failed (${res.status})`);
  return res.blob();
}

// ─── PakWatch API ───

export async function queryWatch(question: string): Promise<WatchResponse> {
  return fetchJson<WatchResponse>(
    `${API_BASE}/api/watch/query`,
    { query: question }
  );
}

export async function searchWatch(query: string): Promise<WatchSearchResult> {
  return fetchJson<WatchSearchResult>(
    `${API_BASE}/api/watch/search`,
    { query }
  );
}

export async function getLatestUpdates(
  category?: string,
  province?: string,
  limit?: number
): Promise<{ updates: Record<string, unknown>[]; count?: number }> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (province) params.set("province", province);
  if (limit) params.set("limit", String(limit));
  return fetchGet(`${API_BASE}/api/watch/latest?${params}`);
}

export async function getCategories(): Promise<{ categories: CategoryCount[] }> {
  return fetchGet(`${API_BASE}/api/watch/categories`);
}

export async function getHotTopics(): Promise<{ topics: HotTopic[] }> {
  return fetchGet(`${API_BASE}/api/watch/topics`);
}

// ─── PakScholar API ───

export async function queryScholar(question: string): Promise<ScholarResponse> {
  return fetchJson<ScholarResponse>(
    `${API_BASE}/api/scholar/query`,
    { query: question }
  );
}

export async function getOpportunities(
  status?: string,
  type?: string,
  province?: string,
  limit?: number
): Promise<{ count: number; data: Opportunity[] }> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (type) params.set("type", type);
  if (province) params.set("province", province);
  if (limit) params.set("limit", String(limit));
  return fetchGet(`${API_BASE}/api/scholar/opportunities?${params}`);
}

// ─── Health ───

export async function getHealth(): Promise<Record<string, unknown>> {
  return fetchGet(`${API_BASE}/health`);
}
