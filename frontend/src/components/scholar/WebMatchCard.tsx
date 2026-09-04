"use client";

import { motion } from "framer-motion";
import {
  HiOutlineCheckCircle,
  HiOutlineXCircle,
  HiOutlineArrowTopRightOnSquare,
  HiOutlineExclamationTriangle,
  HiOutlineClock,
} from "react-icons/hi2";

import type { WebMatch } from "@/types/scholar";

/** Format an ISO datetime like "26 Aug 2026, 14:32 UTC" */
function formatDateTime(raw?: string): string {
  if (!raw) return "";
  const d = new Date(raw);
  if (isNaN(d.getTime())) return raw;
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZoneName: "short",
  });
}

interface Props {
  match: WebMatch;
  index: number;
  detectedLanguage?: string;
}

export default function WebMatchCard({ match, index, detectedLanguage }: Props) {
  const isUrdu = detectedLanguage === "ur";
  const isRelevant = match.relevant === true || match.relevant === "yes";
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.45, ease: "easeOut" }}
      whileHover={{ y: -4, scale: 1.01 }}
      className="glass-card group rounded-2xl p-6 transition-shadow duration-300 hover:shadow-lg hover:shadow-brand-teal/10 border-l-2 border-l-amber-500/40"
    >
      {/* Unverified badge + found date */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mb-3">
        <div className="flex items-center gap-1.5">
          <HiOutlineExclamationTriangle className="h-3.5 w-3.5 text-amber-400" />
          <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400">
            Unverified — confirm on official site
          </span>
        </div>
        {match.found_on && (
          <div className="flex items-center gap-1 text-[10px] text-slate-500">
            <HiOutlineClock className="h-3 w-3" />
            <span>Found: {formatDateTime(match.found_on)}</span>
          </div>
        )}
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-base font-bold text-white leading-snug">
          {match.title}
        </h3>
        {isRelevant ? (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-400 ring-1 ring-emerald-500/30">
            <HiOutlineCheckCircle className="h-3.5 w-3.5" />
            Relevant
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-500/15 px-3 py-1 text-xs font-semibold text-slate-400 ring-1 ring-slate-500/30">
            <HiOutlineXCircle className="h-3.5 w-3.5" />
            Not Relevant
          </span>
        )}
      </div>

      {/* Snippet */}
      {match.snippet && (
        <p className="mt-2 text-xs leading-relaxed text-slate-400 italic">
          {match.snippet}
        </p>
      )}

      {/* Reasoning */}
      <p className={`mt-3 text-sm leading-relaxed text-slate-300 ${
        isUrdu ? "urdu-text" : ""
      }`}>
        {match.reasoning}
      </p>

      {/* Link */}
      {match.url && (
        <div className="mt-4">
          <a
            href={match.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full border border-brand-teal/30 bg-brand-teal/10 px-4 py-2 text-xs font-semibold text-brand-teal transition-all hover:bg-brand-teal/20"
          >
            Visit Link
            <HiOutlineArrowTopRightOnSquare className="h-3.5 w-3.5" />
          </a>
        </div>
      )}
    </motion.div>
  );
}
