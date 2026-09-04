"use client";

import { motion } from "framer-motion";
import { HiOutlineSparkles, HiOutlineBookOpen, HiOutlineEye, HiOutlineAcademicCap } from "react-icons/hi2";
import type { ModuleName, GuideResponse, WatchResponse, ScholarResponse } from "@/lib/api";
import { isUrdu } from "@/lib/smartSearch";

interface SearchResultProps {
  module: ModuleName;
  data: GuideResponse | WatchResponse | ScholarResponse;
}

const MODULE_META: Record<ModuleName, { label: string; icon: React.ReactNode; color: string }> = {
  guide: {
    label: "PakGuide",
    icon: <HiOutlineBookOpen className="h-4 w-4" />,
    color: "text-brand-green",
  },
  watch: {
    label: "PakWatch",
    icon: <HiOutlineEye className="h-4 w-4" />,
    color: "text-brand-teal",
  },
  scholar: {
    label: "PakScholar",
    icon: <HiOutlineAcademicCap className="h-4 w-4" />,
    color: "text-brand-emerald",
  },
};

export default function SearchResult({ module, data }: SearchResultProps) {
  const meta = MODULE_META[module];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass-card mt-6 w-full rounded-2xl border border-brand-green/20 p-6"
    >
      {/* Module badge */}
      <div className="mb-4 flex items-center gap-2">
        <span className={`inline-flex items-center gap-1.5 rounded-full bg-white/5 px-3 py-1 text-xs font-semibold ${meta.color} ring-1 ring-white/10`}>
          {meta.icon}
          {meta.label}
        </span>
        <span className="text-xs text-slate-500">Answered via smart routing</span>
      </div>

      {/* Render based on module type */}
      {module === "guide" && <GuideResult data={data as GuideResponse} />}
      {module === "watch" && <WatchResult data={data as WatchResponse} />}
      {module === "scholar" && <ScholarResult data={data as ScholarResponse} />}
    </motion.div>
  );
}

function GuideResult({ data }: { data: GuideResponse }) {
  const urdu = isUrdu(data.answer);
  return (
    <div className="space-y-4">
      <p className={`text-sm leading-relaxed text-slate-300 ${urdu ? "urdu-text" : ""}`}>
        {data.answer}
      </p>
      {data.requirements.length > 0 && (
        <div>
          <h4 className="mb-1 text-xs font-semibold uppercase text-slate-500">Requirements</h4>
          <ol className="list-decimal space-y-0.5 pl-5 text-sm text-slate-400">
            {data.requirements.map((r, i) => <li key={i}>{r}</li>)}
          </ol>
        </div>
      )}
      {data.steps.length > 0 && (
        <div>
          <h4 className="mb-1 text-xs font-semibold uppercase text-slate-500">Steps</h4>
          <ol className="list-decimal space-y-0.5 pl-5 text-sm text-slate-400">
            {data.steps.map((s, i) => <li key={i}>{s}</li>)}
          </ol>
        </div>
      )}
      {data.fee && (
        <p className="text-sm text-slate-400"><strong className="text-slate-300">Fee:</strong> {data.fee}</p>
      )}
      <ConfidenceBadge confidence={data.confidence} />
    </div>
  );
}

function WatchResult({ data }: { data: WatchResponse }) {
  const urdu = isUrdu(data.answer);
  return (
    <div className="space-y-4">
      <p className={`text-sm leading-relaxed text-slate-300 ${urdu ? "urdu-text" : ""}`}>
        {data.answer}
      </p>
      {data.what_changed && (
        <div className="rounded-lg border border-brand-teal/20 bg-brand-teal/5 p-3">
          <h4 className="text-xs font-semibold uppercase text-brand-teal">What Changed</h4>
          <p className="mt-1 text-sm text-slate-400">{data.what_changed}</p>
        </div>
      )}
      {data.updates.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500">Related Updates</h4>
          <div className="space-y-2">
            {data.updates.slice(0, 3).map((u, i) => (
              <div key={i} className="rounded-lg bg-white/5 p-3 ring-1 ring-white/5">
                <p className="text-sm font-medium text-slate-300">{u.title}</p>
                {u.summary && <p className="mt-0.5 text-xs text-slate-500 line-clamp-2">{u.summary}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
      <ConfidenceBadge confidence={data.confidence} />
    </div>
  );
}

function ScholarResult({ data }: { data: ScholarResponse }) {
  const urdu = data.detected_language === "ur";
  return (
    <div className="space-y-4">
      {data.answer_summary && (
        <div className="flex items-start gap-2">
          <HiOutlineSparkles className="mt-0.5 h-4 w-4 flex-shrink-0 text-brand-emerald" />
          <p className={`text-sm leading-relaxed text-slate-300 ${urdu ? "urdu-text" : ""}`}>
            {data.answer_summary}
          </p>
        </div>
      )}
      {data.database_matches.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500">
            {data.database_matches.length} Opportunities Evaluated
          </h4>
          <div className="space-y-2">
            {data.database_matches.filter(m => m.eligible === true || m.eligible === "maybe").slice(0, 3).map((m, i) => (
              <div key={i} className="rounded-lg bg-white/5 p-3 ring-1 ring-white/5">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium text-slate-300">{m.title}</p>
                  <span className={`flex-shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    m.eligible === true
                      ? "bg-green-500/10 text-green-400 ring-1 ring-green-500/20"
                      : "bg-yellow-500/10 text-yellow-400 ring-1 ring-yellow-500/20"
                  }`}>
                    {m.eligible === true ? "Eligible" : "Maybe"}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-slate-500">{m.reasoning}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {data.web_matches.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase text-amber-400">Web Results (Please Verify)</h4>
          <div className="space-y-2">
            {data.web_matches.slice(0, 2).map((m, i) => (
              <div key={i} className="rounded-lg border border-amber-500/10 bg-amber-500/5 p-3">
                <a href={m.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-brand-teal hover:underline">
                  {m.title}
                </a>
                <p className="mt-0.5 text-xs text-slate-500 line-clamp-2">{m.snippet}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ConfidenceBadge({ confidence }: { confidence: "high" | "medium" | "low" }) {
  const styles = {
    high: "bg-green-500/10 text-green-400 ring-green-500/20",
    medium: "bg-yellow-500/10 text-yellow-400 ring-yellow-500/20",
    low: "bg-red-500/10 text-red-400 ring-red-500/20",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ring-1 ${styles[confidence]}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${
        confidence === "high" ? "bg-green-400" : confidence === "medium" ? "bg-yellow-400" : "bg-red-400"
      }`} />
      {confidence.charAt(0).toUpperCase() + confidence.slice(1)} Confidence
    </span>
  );
}
