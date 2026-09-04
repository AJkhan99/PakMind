"use client";

import type { Source } from "@/types/watch";

interface SourceCardProps {
  source: Source;
}

export function SourceCard({ source }: SourceCardProps) {
  return (
    <div className="glass-card rounded-lg p-3 text-sm">
      <div className="flex items-start gap-2">
        <div className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded bg-pakgreen/10 text-pakgreen">
          <svg
            className="h-3 w-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-medium text-slate-300 truncate">
            {source.title || source.source_name || "Government Source"}
          </p>
          {source.source_name && (
            <p className="text-xs text-slate-500">{source.source_name}</p>
          )}
          <div className="mt-1 flex flex-wrap gap-x-3 text-xs text-slate-600">
            {source.published_date && (
              <span>Published: {formatDate(source.published_date)}</span>
            )}
            {source.last_verified && (
              <span>Verified: {formatDate(source.last_verified)}</span>
            )}
          </div>
          {source.url && (
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 inline-flex items-center gap-1 text-xs text-pakgreen hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              <svg
                className="h-3 w-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
              Official Source
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-PK", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
