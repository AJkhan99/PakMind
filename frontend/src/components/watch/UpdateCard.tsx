"use client";

import { useState } from "react";
import type { GovernmentUpdate } from "@/types/watch";

interface UpdateCardProps {
  update: GovernmentUpdate;
}

const IMPORTANCE_COLORS: Record<string, string> = {
  high: "bg-red-500/10 text-red-400 border-red-500/20",
  medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  low: "bg-slate-500/10 text-slate-400 border-slate-500/20",
};

const IMPORTANCE_DOT: Record<string, string> = {
  high: "bg-red-400",
  medium: "bg-yellow-400",
  low: "bg-slate-400",
};

const CATEGORY_COLORS: Record<string, string> = {
  policy: "bg-blue-500/10 text-blue-400",
  notification: "bg-purple-500/10 text-purple-400",
  announcement: "bg-indigo-500/10 text-indigo-400",
  scheme: "bg-teal-500/10 text-teal-400",
  regulation: "bg-orange-500/10 text-orange-400",
  appointment: "bg-cyan-500/10 text-cyan-400",
  circular: "bg-pink-500/10 text-pink-400",
  public_notice: "bg-amber-500/10 text-amber-400",
  administrative: "bg-slate-500/10 text-slate-400",
  public_service: "bg-emerald-500/10 text-emerald-400",
  other: "bg-slate-500/10 text-slate-400",
};

export function UpdateCard({ update }: UpdateCardProps) {
  const [expanded, setExpanded] = useState(false);

  const importanceClass =
    IMPORTANCE_COLORS[update.importance || "medium"] ||
    IMPORTANCE_COLORS.medium;
  const dotClass =
    IMPORTANCE_DOT[update.importance || "medium"] || IMPORTANCE_DOT.medium;
  const categoryClass =
    CATEGORY_COLORS[update.category || "other"] || CATEGORY_COLORS.other;

  return (
    <div
      className="glass-card rounded-xl p-4 transition hover:border-pakgreen/20 cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      {/* Top row: badges */}
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span
          className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${importanceClass}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} />
          {update.importance || "medium"}
        </span>

        {update.category && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${categoryClass}`}
          >
            {formatLabel(update.category)}
          </span>
        )}

        {update.province && (
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-slate-400 ring-1 ring-white/10">
            {update.province}
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-slate-200 leading-snug">
        {update.title || "Untitled Update"}
      </h3>

      {/* Meta line */}
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
        {update.organization && <span>{update.organization}</span>}
        {update.department && <span>{update.department}</span>}
        {update.published_date && (
          <span className="text-slate-600">
            {formatDate(update.published_date)}
          </span>
        )}
      </div>

      {/* Summary */}
      {update.summary && (
        <p className="mt-2 text-sm text-slate-400 leading-relaxed line-clamp-3">
          {update.summary}
        </p>
      )}

      {/* Expanded details */}
      {expanded && (
        <div className="mt-4 space-y-3 border-t border-white/10 pt-3">
          {update.what_changed && (
            <div>
              <h4 className="text-xs font-semibold uppercase text-pakgreen">
                What Changed
              </h4>
              <p className="mt-1 text-sm text-slate-400">
                {update.what_changed}
              </p>
            </div>
          )}

          {update.effective_date && (
            <div>
              <h4 className="text-xs font-semibold uppercase text-slate-500">
                Effective Date
              </h4>
              <p className="mt-0.5 text-sm text-slate-400">
                {formatDate(update.effective_date)}
              </p>
            </div>
          )}

          {update.affected_groups && update.affected_groups.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold uppercase text-slate-500">
                Who Is Affected
              </h4>
              <div className="mt-1 flex flex-wrap gap-1">
                {update.affected_groups.map((g, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-pakgreen/10 px-2 py-0.5 text-xs text-pakgreen ring-1 ring-pakgreen/20"
                  >
                    {g}
                  </span>
                ))}
              </div>
            </div>
          )}

          {update.important_details &&
            update.important_details.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold uppercase text-slate-500">
                  Key Details
                </h4>
                <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-slate-400">
                  {update.important_details.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
        </div>
      )}

      {/* Expand indicator */}
      <div className="mt-2 text-center">
        <span className="text-xs text-slate-600">
          {expanded ? "Click to collapse" : "Click for details"}
        </span>
      </div>
    </div>
  );
}

function formatLabel(s: string): string {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
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
