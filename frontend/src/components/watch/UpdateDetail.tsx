"use client";

import type { GovernmentUpdate } from "@/types/watch";

interface UpdateDetailProps {
  update: GovernmentUpdate;
  onClose: () => void;
}

export function UpdateDetail({ update, onClose }: UpdateDetailProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="glass-card max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-xl p-6">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <h2 className="text-lg font-bold text-white">
            {update.title || "Untitled Update"}
          </h2>
          <button
            onClick={onClose}
            className="shrink-0 rounded-lg p-1 text-slate-500 hover:bg-white/10 hover:text-slate-300 transition-colors"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Badges */}
        <div className="mt-3 flex flex-wrap gap-2">
          {update.category && (
            <Badge color="blue">{formatLabel(update.category)}</Badge>
          )}
          {update.province && <Badge color="gray">{update.province}</Badge>}
          {update.importance && (
            <Badge
              color={
                update.importance === "high"
                  ? "red"
                  : update.importance === "medium"
                  ? "yellow"
                  : "gray"
              }
            >
              {update.importance} importance
            </Badge>
          )}
        </div>

        {/* Body */}
        <div className="mt-5 space-y-4">
          {update.summary && (
            <Section title="Summary">
              <p className="text-sm text-slate-400 leading-relaxed">
                {update.summary}
              </p>
            </Section>
          )}

          {update.what_changed && (
            <Section title="What Changed" highlight>
              <p className="text-sm text-slate-400 leading-relaxed">
                {update.what_changed}
              </p>
            </Section>
          )}

          <div className="grid grid-cols-2 gap-4">
            {update.organization && (
              <Section title="Organization">
                <p className="text-sm text-slate-400">{update.organization}</p>
              </Section>
            )}
            {update.department && (
              <Section title="Department">
                <p className="text-sm text-slate-400">{update.department}</p>
              </Section>
            )}
            {update.published_date && (
              <Section title="Published">
                <p className="text-sm text-slate-400">
                  {formatDate(update.published_date)}
                </p>
              </Section>
            )}
            {update.effective_date && (
              <Section title="Effective Date">
                <p className="text-sm text-slate-400">
                  {formatDate(update.effective_date)}
                </p>
              </Section>
            )}
          </div>

          {update.affected_groups && update.affected_groups.length > 0 && (
            <Section title="Who Is Affected">
              <div className="flex flex-wrap gap-1">
                {update.affected_groups.map((g, i) => (
                  <span
                    key={i}
                    className="rounded-full bg-pakgreen/10 px-2.5 py-0.5 text-xs text-pakgreen ring-1 ring-pakgreen/20"
                  >
                    {g}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {update.important_details &&
            update.important_details.length > 0 && (
              <Section title="Key Details">
                <ul className="list-inside list-disc space-y-1 text-sm text-slate-400">
                  {update.important_details.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </Section>
            )}
        </div>

        {/* Close button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-white/5 px-4 py-2 text-sm text-slate-300 ring-1 ring-white/10 transition hover:bg-white/10"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  highlight,
  children,
}: {
  title: string;
  highlight?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div
      className={`rounded-lg p-3 ${
        highlight
          ? "border border-pakgreen/20 bg-pakgreen/5"
          : "border border-white/10 bg-white/5"
      }`}
    >
      <h4
        className={`text-xs font-semibold uppercase ${
          highlight ? "text-pakgreen" : "text-slate-500"
        }`}
      >
        {title}
      </h4>
      <div className="mt-1">{children}</div>
    </div>
  );
}

function Badge({
  color,
  children,
}: {
  color: string;
  children: React.ReactNode;
}) {
  const colorMap: Record<string, string> = {
    blue: "bg-blue-500/10 text-blue-400",
    red: "bg-red-500/10 text-red-400",
    yellow: "bg-yellow-500/10 text-yellow-400",
    gray: "bg-slate-500/10 text-slate-400",
    green: "bg-green-500/10 text-green-400",
  };
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
        colorMap[color] || colorMap.gray
      }`}
    >
      {children}
    </span>
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
