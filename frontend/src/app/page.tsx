"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  HiOutlineSparkles,
  HiOutlineShieldCheck,
  HiOutlineExclamationTriangle,
} from "react-icons/hi2";

import AnimatedBackground from "@/components/AnimatedBackground";
import SmartSearchBar from "@/components/SmartSearchBar";
import ModuleCard from "@/components/ModuleCard";
import SearchResult from "@/components/SearchResult";
import LoadingIndicator from "@/components/LoadingIndicator";
import type { ModuleName, GuideResponse, WatchResponse, ScholarResponse } from "@/lib/api";

/* ── Module internal routes ── */
const MODULES = [
  {
    module: "guide" as ModuleName,
    title: "PakGuide",
    subtitle: "Government Services",
    description:
      "Get verified answers about passport, CNIC, domicile, driving licence, and 17+ government services with fee calculators and office locators.",
    href: "/guide",
  },
  {
    module: "watch" as ModuleName,
    title: "PakWatch",
    subtitle: "Government Updates",
    description:
      "Monitor policy changes, notifications, petrol prices, budget updates, and regulatory announcements from official sources.",
    href: "/watch",
  },
  {
    module: "scholar" as ModuleName,
    title: "PakScholar",
    subtitle: "Scholarship Matcher",
    description:
      "AI-powered scholarship matching for Pakistani students — find opportunities you're eligible for, from HEC to Fulbright.",
    href: "/scholar",
  },
];

export default function PakMindHome() {
  const [result, setResult] = useState<{
    module: ModuleName;
    data: GuideResponse | WatchResponse | ScholarResponse;
  } | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleResult = useCallback(
    (module: ModuleName, data: GuideResponse | WatchResponse | ScholarResponse) => {
      setResult({ module, data });
    },
    []
  );

  return (
    <>
      <AnimatedBackground />

      <main className="relative z-10 mx-auto flex min-h-screen w-full max-w-4xl flex-col items-center px-5 py-12 sm:px-8">
        {/* ─── Hero Section ─── */}
        <motion.header
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="mt-8 flex flex-col items-center text-center"
        >
          {/* Badge */}
          <div className="mb-5 flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-slate-300 backdrop-blur">
            <HiOutlineShieldCheck className="h-4 w-4 text-brand-green" />
            Pakistan&apos;s AI Knowledge Platform
          </div>

          {/* Title */}
          <h1 className="gradient-text text-6xl font-extrabold tracking-tight sm:text-7xl lg:text-8xl">
            PakMind
          </h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="mt-4 max-w-xl text-base leading-relaxed text-slate-400 sm:text-lg"
          >
            Your AI-powered companion for government services, policy updates,
            and scholarship matching — all in one place.
          </motion.p>

          {/* Feature chips */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.4 }}
            className="mt-5 flex flex-wrap justify-center gap-2"
          >
            <FeatureChip label="English" />
            <FeatureChip label="Roman Urdu" />
            <FeatureChip label="اردو" isUrdu />
            <FeatureChip label="Voice Input" />
            <FeatureChip label="AI Verified" />
          </motion.div>
        </motion.header>

        {/* ─── Smart Search Bar ─── */}
        <div className="mt-10 w-full">
          <SmartSearchBar
            onResult={handleResult}
            onError={setError}
            onLoading={setLoading}
          />
        </div>

        {/* Bilingual hint */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.4 }}
          className="mt-3 text-xs text-slate-500"
        >
          Smart search automatically routes your question to the right module
        </motion.p>

        {/* ─── Loading ─── */}
        <AnimatePresence mode="wait">
          {loading && <LoadingIndicator />}
        </AnimatePresence>

        {/* ─── Error ─── */}
        <AnimatePresence>
          {error && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass-card mt-6 w-full rounded-2xl border border-amber-500/20 p-6 text-center"
            >
              <HiOutlineExclamationTriangle className="mx-auto mb-3 h-8 w-8 text-amber-400" />
              <p className="text-sm leading-relaxed text-slate-300">{error}</p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── Search Result ─── */}
        <AnimatePresence>
          {result && !loading && (
            <div className="w-full">
              <SearchResult module={result.module} data={result.data} />
            </div>
          )}
        </AnimatePresence>

        {/* ─── Module Cards ─── */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.5 }}
          className="mt-16 w-full"
        >
          <div className="mb-6 text-center">
            <h2 className="text-lg font-bold text-white">
              Explore Specialized Modules
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Click on a module for the full dedicated experience
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {MODULES.map((m, i) => (
              <ModuleCard
                key={m.module}
                module={m.module}
                title={m.title}
                subtitle={m.subtitle}
                description={m.description}
                href={m.href}
                index={i}
              />
            ))}
          </div>
        </motion.section>

        {/* ─── Footer ─── */}
        <footer className="mt-auto pt-16 pb-6 text-center text-xs text-slate-600">
          PakMind &middot; Built for Pakistan &middot; Powered by Gemini AI
        </footer>
      </main>
    </>
  );
}

/* ── Small helper component ── */
function FeatureChip({ label, isUrdu }: { label: string; isUrdu?: boolean }) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400">
      <span className={isUrdu ? "font-semibold" : ""} style={isUrdu ? { fontFamily: "var(--font-nastaliq), serif" } : undefined}>
        {label}
      </span>
    </span>
  );
}
