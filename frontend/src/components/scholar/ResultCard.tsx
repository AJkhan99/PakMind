"use client";

import { motion } from "framer-motion";
import {
  HiOutlineCalendarDays,
  HiOutlineCheckCircle,
  HiOutlineExclamationCircle,
  HiOutlineXCircle,
  HiOutlineArrowTopRightOnSquare,
  HiOutlineShieldCheck,
} from "react-icons/hi2";

import type { Match } from "@/types/scholar";

/** Format an ISO date string like "26 Aug 2026" */
function formatDate(raw?: string | null): string {
  if (!raw) return "N/A";
  const d = new Date(raw);
  if (isNaN(d.getTime())) return raw;
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

interface Props {
  match: Match;
  index: number;
  detectedLanguage?: string;
}

function Badge({ eligible }: { eligible: boolean | string }) {
  if (eligible === true || eligible === "yes") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-400 ring-1 ring-emerald-500/30">
        <HiOutlineCheckCircle className="h-3.5 w-3.5" />
        Eligible
      </span>
    );
  }
  if (eligible === "maybe") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 px-3 py-1 text-xs font-semibold text-amber-400 ring-1 ring-amber-500/30">
        <HiOutlineExclamationCircle className="h-3.5 w-3.5" />
        Maybe
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-3 py-1 text-xs font-semibold text-red-400 ring-1 ring-red-500/30">
      <HiOutlineXCircle className="h-3.5 w-3.5" />
      Not Eligible
    </span>
  );
}

export default function ResultCard({ match, index, detectedLanguage }: Props) {
  const isUrdu = detectedLanguage === "ur";
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.45, ease: "easeOut" }}
      whileHover={{ y: -4, scale: 1.01 }}
      className="glass-card group rounded-2xl p-6 transition-shadow duration-300 hover:shadow-lg hover:shadow-brand-green/10"
    >
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <h3 className="text-lg font-bold text-white leading-snug">
            {match.title}
          </h3>
          <p className="text-sm text-slate-400">{match.organization}</p>
          {/* Meta tags */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {match.type && (
              <span className="rounded-full bg-brand-green/10 px-2 py-0.5 text-[10px] font-medium text-brand-green ring-1 ring-brand-green/20">
                {match.type}
              </span>
            )}
            {match.province && (
              <span className="rounded-full bg-brand-teal/10 px-2 py-0.5 text-[10px] font-medium text-brand-teal ring-1 ring-brand-teal/20">
                {match.province}
              </span>
            )}
            {match.degree_level && (
              <span className="rounded-full bg-brand-emerald/10 px-2 py-0.5 text-[10px] font-medium text-brand-emerald ring-1 ring-brand-emerald/20">
                {match.degree_level}
              </span>
            )}
            {match.amount && (
              <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] font-medium text-slate-400 ring-1 ring-white/10">
                {match.amount}
              </span>
            )}
          </div>
        </div>
        <Badge eligible={match.eligible} />
      </div>

      {/* Reasoning */}
      <p className={`mt-4 text-sm leading-relaxed text-slate-300 ${
        isUrdu ? "urdu-text" : ""
      }`}>
        {match.reasoning}
      </p>

      {/* Footer */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        {/* Deadline */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400">
          <HiOutlineCalendarDays className="h-4 w-4 text-brand-teal" />
          <span>Deadline: {formatDate(match.deadline)}</span>
        </div>

        {/* Apply button */}
        {match.application_url && (
          <a
            href={match.application_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-gradient inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold text-white"
          >
            Apply Now
            <HiOutlineArrowTopRightOnSquare className="h-3.5 w-3.5" />
          </a>
        )}
      </div>

      {/* Verified date stamp */}
      {match.last_verified && (
        <div className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-500">
          <HiOutlineShieldCheck className="h-3.5 w-3.5 text-emerald-500/60" />
          <span>Verified: {formatDate(match.last_verified)}</span>
        </div>
      )}
    </motion.div>
  );
}
