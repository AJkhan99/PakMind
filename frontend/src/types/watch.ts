/** TypeScript types for the PakWatch module in PakMind. */

export interface Source {
  title: string | null;
  url: string | null;
  source_name: string | null;
  published_date: string | null;
  last_verified: string | null;
}

export interface GovernmentUpdate {
  id?: string;
  title: string | null;
  category: string | null;
  department: string | null;
  province: string | null;
  organization?: string | null;
  summary: string | null;
  importance: string | null;
  published_date: string | null;
  what_changed: string | null;
  affected_groups?: string[];
  important_details?: string[];
  effective_date?: string | null;
  status?: string | null;
}

export interface QueryResponse {
  module: string;
  answer: string;
  updates: GovernmentUpdate[];
  sources: Source[];
  what_changed: string | null;
  who_affected: string | null;
  effective_date: string | null;
  last_verified: string | null;
  confidence: "high" | "medium" | "low";
  warnings: string[];
}

export interface SearchResponse {
  module: string;
  query: string;
  results: GovernmentUpdate[];
}

export interface LatestResponse {
  module: string;
  updates: GovernmentUpdate[];
}

export interface CategoryInfo {
  category: string;
  count: number;
}

export interface CategoriesResponse {
  module: string;
  categories: CategoryInfo[];
}

export interface TopicDigest {
  id?: string;
  topic: string;
  query: string;
  answer: string | null;
  what_changed: string | null;
  who_affected: string | null;
  effective_date: string | null;
  confidence: "high" | "medium" | "low";
  update_ids?: string[];
  sources?: Source[];
  generated_at: string | null;
}

export interface TopicsResponse {
  module: string;
  topics: TopicDigest[];
  count: number;
}

export interface Filters {
  category: string;
  province: string;
  importance: string;
}

export const CATEGORIES = [
  "All",
  "policy",
  "notification",
  "announcement",
  "scheme",
  "regulation",
  "appointment",
  "circular",
  "public_notice",
  "administrative",
  "public_service",
  "other",
] as const;

export const PROVINCES = [
  "All",
  "Federal",
  "Punjab",
  "Sindh",
  "Khyber Pakhtunkhwa",
  "Balochistan",
  "Islamabad Capital Territory",
  "Azad Jammu & Kashmir",
  "Gilgit-Baltistan",
] as const;

export const IMPORTANCE_LEVELS = ["All", "high", "medium", "low"] as const;
