"use client";

import type { GuideResponse } from "@/types/guide";
import { RequirementList } from "./RequirementList";
import { StepsList } from "./StepsList";
import { SourceCard } from "./SourceCard";
import { VerificationBadge } from "./VerificationBadge";
import { FeedbackButtons } from "./FeedbackButtons";
import { PrintableChecklist } from "./PrintableChecklist";
import { OfficeLocator } from "./OfficeLocator";
import { speakText } from "./VoiceInput";

interface AnswerCardProps {
  data: GuideResponse;
  query: string;
}

export function AnswerCard({ data, query }: AnswerCardProps) {
  return (
    <div className="glass-card space-y-6 rounded-xl p-6">
      {/* Header row */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-base leading-relaxed text-slate-300" dir="auto">
            {data.answer}
          </p>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            {/* Listen button */}
            <button
              onClick={() => speakText(data.answer)}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/5 px-2.5 py-1
                         text-xs text-slate-400 hover:border-pakgreen/30 hover:text-pakgreen transition-colors"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
              Listen
            </button>
            {/* Source type badge */}
            <SourceTypeBadge sourceType={data.source_type} />
          </div>
        </div>
        <VerificationBadge confidence={data.confidence} />
      </div>

      {/* Eligibility */}
      {data.eligibility && (
        <Section title="Eligibility">
          <p className="text-sm text-slate-400">{data.eligibility}</p>
        </Section>
      )}

      {/* Required Documents */}
      {data.requirements.length > 0 && (
        <Section title="Required Documents">
          <RequirementList items={data.requirements} />
        </Section>
      )}

      {/* Steps */}
      {data.steps.length > 0 && (
        <Section title="Steps / Procedure">
          <StepsList items={data.steps} />
        </Section>
      )}

      {/* Details grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {data.fee && (
          <DetailCard label="Fee" value={data.fee} />
        )}
        {data.processing_time && (
          <DetailCard label="Processing Time" value={data.processing_time} />
        )}
        {data.application_method && (
          <DetailCard label="Application Method" value={data.application_method} />
        )}
        {data.application_url && (
          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
            <p className="text-xs font-medium text-slate-500">Application URL</p>
            <a
              href={data.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-pakgreen hover:underline break-all"
            >
              {data.application_url}
            </a>
          </div>
        )}
      </div>

      {/* Sources */}
      {data.sources.length > 0 && (
        <Section title="Official Sources">
          <div className="space-y-2">
            {data.sources.map((src, i) => (
              <SourceCard key={i} source={src} />
            ))}
          </div>
        </Section>
      )}

      {/* Office Locator */}
      <OfficeLocator
        contactInfo={data.contact_info}
        answer={data.answer}
        query={query}
      />

      {/* Printable Checklist + Fee Calculator */}
      {(data.requirements.length > 0 || data.fee) && (
        <PrintableChecklist data={data} query={query} />
      )}

      {/* Feedback */}
      <FeedbackButtons
        query={query}
        responseSnapshot={data as unknown as Record<string, unknown>}
      />
    </div>
  );
}

/* ---------- Sub-components ---------- */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
        {title}
      </h3>
      {children}
    </div>
  );
}

function DetailCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
      <p className="text-xs font-medium text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm font-medium text-slate-300">{value}</p>
    </div>
  );
}

function SourceTypeBadge({ sourceType }: { sourceType?: string }) {
  if (!sourceType || sourceType === "none") return null;

  const config: Record<string, { label: string; color: string; icon: string }> = {
    database: {
      label: "Verified DB",
      color: "bg-green-500/10 text-green-400 border-green-500/20",
      icon: "🗄️",
    },
    gov_page: {
      label: "Gov Website",
      color: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      icon: "🏛️",
    },
    web: {
      label: "Web Search",
      color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
      icon: "🌐",
    },
    mixed: {
      label: "Multiple Sources",
      color: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      icon: "📚",
    },
  };

  const c = config[sourceType] || config.web;

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${c.color}`}>
      <span>{c.icon}</span>
      {c.label}
    </span>
  );
}
