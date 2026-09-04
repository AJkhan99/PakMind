"use client";

import { useState, useRef, useEffect, FormEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  HiOutlineMagnifyingGlass,
  HiOutlineSparkles,
  HiOutlineAcademicCap,
  HiOutlineGlobeAlt,
  HiOutlineExclamationTriangle,
  HiOutlineArrowPath,
} from "react-icons/hi2";
import Link from "next/link";

import AnimatedBackground from "@/components/AnimatedBackground";
import LoadingIndicator from "@/components/LoadingIndicator";
import ResultCard from "@/components/scholar/ResultCard";
import WebMatchCard from "@/components/scholar/WebMatchCard";
import { queryScholar, type ScholarResponse } from "@/lib/api";
import type { Match, WebMatch } from "@/types/scholar";

export default function ScholarPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ScholarResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [slow, setSlow] = useState(false);

  /* Track the last query so "Try Again" can re-run it */
  const lastQueryRef = useRef("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /* Clean up the timeout timer on unmount */
  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  async function handleSearch(e?: FormEvent) {
    if (e) e.preventDefault();
    const q = query.trim() || lastQueryRef.current;
    if (!q) return;

    lastQueryRef.current = q;
    setLoading(true);
    setError(null);
    setResults(null);
    setSlow(false);

    /* 15-second timeout — show a "taking long" message */
    timerRef.current = setTimeout(() => setSlow(true), 15000);

    try {
      const data = await queryScholar(q);

      /* Backend returned a structured error response */
      if (data.error === true) {
        const msg =
          data.message || "Something went wrong. Please try again.";
        setError(msg);
        return;
      }

      setResults(data);
    } catch (err) {
      /* Backend is unreachable or returned an error */
      const message =
        err instanceof Error ? err.message : "Unknown error";
      if (message.includes("API error")) {
        setError(message);
      } else {
        setError(
          "Can\u2019t connect to PakScholar right now. Please make sure the app is running and try again."
        );
      }
    } finally {
      if (timerRef.current) clearTimeout(timerRef.current);
      setLoading(false);
      setSlow(false);
    }
  }

  // Whether both result sets are empty (for the friendly no-results message)
  const bothEmpty =
    results &&
    !loading &&
    results.database_matches.length === 0 &&
    results.web_matches.length === 0;

  return (
    <>
      <AnimatedBackground />

      <main className="relative z-10 mx-auto flex min-h-screen w-full max-w-3xl flex-col items-center px-5 py-12 sm:px-8">
        {/* ─── Back to Home ─── */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full"
        >
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-slate-400 backdrop-blur transition-colors hover:bg-white/10 hover:text-white"
          >
            ← Back to Home
          </Link>
        </motion.div>

        {/* ─── Header ─── */}
        <motion.header
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className="mt-8 flex flex-col items-center text-center"
        >
          <div className="mb-4 flex items-center gap-2.5 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-slate-300 backdrop-blur">
            <HiOutlineAcademicCap className="h-4 w-4 text-brand-teal" />
            AI-Powered Scholarship Matcher
          </div>

          <h1 className="gradient-text text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
            PakScholar
          </h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="mt-4 max-w-xl text-base leading-relaxed text-slate-400 sm:text-lg"
          >
            Find scholarships &amp; internships you&apos;re eligible for —
            powered by AI
          </motion.p>
        </motion.header>

        {/* ─── Search ─── */}
        <motion.form
          onSubmit={handleSearch}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="mt-10 flex w-full flex-col gap-3 sm:flex-row"
        >
          <div className="relative flex-1">
            <HiOutlineMagnifyingGlass className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. I'm a BS CS student from Punjab with 78% marks"
              className="glow-input w-full rounded-2xl border border-white/10 bg-white/5 py-4 pl-12 pr-4 text-sm text-white placeholder-slate-500 outline-none backdrop-blur transition-shadow focus:border-brand-green/50"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-gradient flex items-center justify-center gap-2 rounded-2xl px-8 py-4 text-sm font-semibold text-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <HiOutlineSparkles className="h-4 w-4" />
            Search
          </button>
        </motion.form>

        {/* ─── Bilingual hint ─── */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7, duration: 0.4 }}
          className="mt-3 text-xs text-slate-500"
        >
          Ask in English or{" "}
          <span
            className="font-semibold text-slate-400"
            style={{ fontFamily: "var(--font-nastaliq), serif" }}
          >
            اردو
          </span>
        </motion.p>

        {/* ─── Loading ─── */}
        <AnimatePresence mode="wait">
          {loading && (
            <div key="loading-wrap">
              <LoadingIndicator label="Matching your eligibility…" />
              {slow && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="mt-3 text-center text-xs text-amber-400"
                >
                  This is taking longer than usual...
                </motion.p>
              )}
            </div>
          )}
        </AnimatePresence>

        {/* ─── Error card ─── */}
        <AnimatePresence>
          {error && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass-card mt-8 w-full rounded-2xl border border-amber-500/20 p-8 text-center"
            >
              <HiOutlineExclamationTriangle className="mx-auto h-10 w-10 text-amber-400 mb-4" />
              <p className="text-sm leading-relaxed text-slate-300 mb-5">
                {error}
              </p>
              <button
                onClick={() => handleSearch()}
                className="btn-gradient inline-flex items-center gap-2 rounded-full px-6 py-2.5 text-sm font-semibold text-white"
              >
                <HiOutlineArrowPath className="h-4 w-4" />
                Try Again
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── No results message ─── */}
        <AnimatePresence>
          {bothEmpty && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass-card mt-8 w-full rounded-xl border border-slate-500/20 p-8 text-center"
            >
              <HiOutlineExclamationTriangle className="mx-auto h-8 w-8 text-slate-500 mb-3" />
              <p className="text-sm text-slate-300">
                No matches found yet — check back later or try adjusting your
                details.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ─── Results ─── */}
        <AnimatePresence>
          {results && !loading && !bothEmpty && (
            <motion.section
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4 }}
              className="mt-10 w-full space-y-8"
            >
              {/* ═══ Verified Opportunities ═══ */}
              {results.database_matches.length > 0 && (
                <div className="space-y-5">
                  {/* Section heading */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4 }}
                    className="flex items-center gap-3"
                  >
                    <span className="text-2xl" aria-hidden="true">✅</span>
                    <h2 className="text-xl font-bold text-white">
                      Verified Opportunities
                    </h2>
                    <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-brand-green/10 px-2.5 py-0.5 text-[10px] font-semibold text-brand-green ring-1 ring-brand-green/20">
                      <HiOutlineAcademicCap className="h-3 w-3" />
                      Database
                    </span>
                  </motion.div>

                  {/* AI summary card */}
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="glass-card rounded-2xl border border-brand-green/20 p-6"
                  >
                    <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-brand-green">
                      <HiOutlineSparkles className="h-4 w-4" />
                      AI Summary
                    </div>
                    <p
                      className={`text-sm leading-relaxed text-slate-300 ${
                        results.detected_language === "ur" ? "urdu-text" : ""
                      }`}
                    >
                      {results.answer_summary}
                    </p>
                  </motion.div>

                  {/* Result count */}
                  <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                    {results.database_matches.length} opportunities evaluated
                  </p>

                  {/* Cards */}
                  <div className="space-y-4">
                    {results.database_matches.map((match, i) => (
                      <ResultCard
                        key={`${match.title}-${i}`}
                        match={match as Match}
                        index={i}
                        detectedLanguage={results.detected_language}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* ═══ Found on the Web (Please Verify) ═══ */}
              {results.web_matches.length > 0 && (
                <div className="space-y-5">
                  {/* Section heading */}
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: 0.15 }}
                    className="flex items-center gap-3"
                  >
                    <span className="text-2xl" aria-hidden="true">🌐</span>
                    <h2 className="text-xl font-bold text-white">
                      Found on the Web{" "}
                      <span className="text-amber-400 font-medium text-base">
                        (Please Verify)
                      </span>
                    </h2>
                    <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-[10px] font-semibold text-amber-400 ring-1 ring-amber-500/20">
                      <HiOutlineExclamationTriangle className="h-3 w-3" />
                      Unverified
                    </span>
                  </motion.div>

                  {/* Web summary card */}
                  {results.web_summary && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: 0.25 }}
                      className="glass-card rounded-2xl border border-amber-500/20 p-6"
                    >
                      <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-400">
                        <HiOutlineGlobeAlt className="h-4 w-4" />
                        Web Summary
                      </div>
                      <p
                        className={`text-sm leading-relaxed text-slate-300 ${
                          results.detected_language === "ur" ? "urdu-text" : ""
                        }`}
                      >
                        {results.web_summary}
                      </p>
                    </motion.div>
                  )}

                  {/* Web result count */}
                  <p className="text-xs font-medium uppercase tracking-wider text-slate-500">
                    {results.web_matches.length} web results found
                  </p>

                  {/* Web match cards */}
                  <div className="space-y-4">
                    {results.web_matches.map((match, i) => (
                      <WebMatchCard
                        key={`web-${match.title}-${i}`}
                        match={match as WebMatch}
                        index={i}
                        detectedLanguage={results.detected_language}
                      />
                    ))}
                  </div>
                </div>
              )}
            </motion.section>
          )}
        </AnimatePresence>

        {/* ─── Footer ─── */}
        <footer className="mt-auto pt-16 pb-6 text-center text-xs text-slate-600">
          PakScholar &middot; Built for Pakistan &middot; Powered by Gemini AI
        </footer>
      </main>
    </>
  );
}
