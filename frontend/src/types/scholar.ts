/**
 * PakScholar types — mirrors the ScholarResponse shape from @/lib/api
 * with additional fields used by the UI components.
 */

// Re-export the canonical ScholarResponse from the API client
export type { ScholarResponse } from "@/lib/api";

/** A verified database opportunity (scholarship / internship). */
export interface Match {
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
  status?: string;
  last_verified?: string;
}

/** An unverified web-search result. */
export interface WebMatch {
  title: string;
  url: string;
  snippet: string;
  relevant: boolean | string;
  reasoning: string;
  found_on?: string;
}
