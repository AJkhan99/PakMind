"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { ModuleName } from "@/lib/api";
import {
  HiOutlineBookOpen,
  HiOutlineEye,
  HiOutlineAcademicCap,
} from "react-icons/hi2";

interface ModuleCardProps {
  module: ModuleName;
  title: string;
  subtitle: string;
  description: string;
  href: string;
  index: number;
}

const ICONS: Record<ModuleName, React.ReactNode> = {
  guide: <HiOutlineBookOpen className="h-7 w-7 text-brand-green" />,
  watch: <HiOutlineEye className="h-7 w-7 text-brand-teal" />,
  scholar: <HiOutlineAcademicCap className="h-7 w-7 text-brand-emerald" />,
};

const ACCENT: Record<ModuleName, string> = {
  guide: "from-brand-green/20 to-brand-green/5",
  watch: "from-brand-teal/20 to-brand-teal/5",
  scholar: "from-brand-emerald/20 to-brand-emerald/5",
};

export default function ModuleCard({
  module,
  title,
  subtitle,
  description,
  href,
  index,
}: ModuleCardProps) {
  return (
    <Link href={href}>
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 + index * 0.15, duration: 0.5 }}
      className={`glass-card module-card-glow group relative flex flex-col gap-3 rounded-2xl p-6 cursor-pointer`}
    >
      {/* Accent gradient overlay */}
      <div
        className={`pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-br ${ACCENT[module]} opacity-0 transition-opacity group-hover:opacity-100`}
      />

      {/* Icon */}
      <div className="relative flex items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/5 ring-1 ring-white/10">
          {ICONS[module]}
        </div>
        <div className="relative">
          <h3 className="text-base font-bold text-white">{title}</h3>
          <p className="text-xs text-slate-500">{subtitle}</p>
        </div>
      </div>

      {/* Description */}
      <p className="relative text-sm leading-relaxed text-slate-400">
        {description}
      </p>

      {/* Arrow hint */}
      <div className="relative mt-auto flex items-center gap-1 text-xs font-medium text-slate-500 transition-colors group-hover:text-brand-green">
        Open module
        <svg
          className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 7l5 5m0 0l-5 5m5-5H6"
          />
        </svg>
      </div>
    </motion.div>
    </Link>
  );
}
