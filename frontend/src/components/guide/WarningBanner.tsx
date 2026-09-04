"use client";

import type { GuideContactInfo } from "@/types/guide";

interface WarningBannerProps {
  warnings: string[];
  contactInfo: Record<string, unknown> | GuideContactInfo | null;
}

/** Safely extract a string field from a possibly-untyped record. */
function str(val: unknown): string | undefined {
  return typeof val === "string" ? val : undefined;
}

export function WarningBanner({ warnings, contactInfo }: WarningBannerProps) {
  const phone = str(contactInfo?.phone);
  const email = str(contactInfo?.email);
  const address = str(contactInfo?.address);
  const hasContact = phone || email || address;

  return (
    <div className="glass-card rounded-xl border border-amber-500/20 p-4">
      <div className="flex items-start gap-3">
        <svg
          className="h-5 w-5 flex-shrink-0 text-amber-400 mt-0.5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"
          />
        </svg>
        <div className="space-y-1">
          <p className="text-sm font-semibold text-amber-400">
            Important Notice
          </p>
          <ul className="list-disc space-y-0.5 pl-4 text-sm text-amber-300/80">
            {warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>

          {hasContact && (
            <div className="mt-3 rounded-lg border border-white/10 bg-white/5 p-3">
              <p className="text-xs font-semibold text-slate-400 mb-1">
                Contact the department directly for verification:
              </p>
              {phone && (
                <p className="text-sm text-slate-300">
                  Phone:{" "}
                  <a href={`tel:${phone}`} className="font-medium text-pakgreen hover:underline">
                    {phone}
                  </a>
                </p>
              )}
              {email && (
                <p className="text-sm text-slate-300">
                  Email:{" "}
                  <a href={`mailto:${email}`} className="font-medium text-pakgreen hover:underline">
                    {email}
                  </a>
                </p>
              )}
              {address && (
                <p className="text-sm text-slate-300">Address: {address}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
