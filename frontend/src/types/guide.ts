/**
 * PakGuide types for the unified PakMind frontend.
 *
 * Re-uses the canonical GuideResponse from @/lib/api and adds
 * helper types used by the guide sub-components.
 */

import type { GuideResponse } from "@/lib/api";

/** Re-export the main response type for convenience. */
export type { GuideResponse };

/** Source citation shape used in guide components. */
export interface GuideSource {
  title: string | null;
  url: string | null;
  source_name: string | null;
}

/** Contact info shape used in guide components. */
export interface GuideContactInfo {
  phone?: string;
  email?: string;
  address?: string;
  website?: string;
}
