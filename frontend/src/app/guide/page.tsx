"use client";

import { useState } from "react";
import Link from "next/link";
import { queryGuide } from "@/lib/api";
import type { GuideResponse } from "@/lib/api";
import { ChatBox } from "@/components/guide/ChatBox";
import { AnswerCard } from "@/components/guide/AnswerCard";
import { WarningBanner } from "@/components/guide/WarningBanner";

const EXAMPLE_QUERIES = [
  "How do I get a domicile in Rawalpindi?",
  "passport banwane ka tarika",
  "CNIC kaise banwayen?",
  "driving licence ka kya procedure hai?",
  "birth certificate ke liye kya chahiye?",
  "police character certificate kahan se milega?",
];

export default function PakGuidePage() {
  const [response, setResponse] = useState<GuideResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState("");

  async function handleAsk(question: string) {
    setLoading(true);
    setError(null);
    setResponse(null);
    setCurrentQuery(question);

    try {
      const data = await queryGuide(question);
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unknown error occurred.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-4xl px-5 py-8 sm:px-8">
      {/* Back to Home */}
      <Link
        href="/"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-pakgreen transition-colors"
      >
        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Home
      </Link>

      <div className="space-y-8">
        {/* Hero */}
        <section className="text-center">
          <h2 className="text-3xl font-bold gradient-text">
            Ask about Pakistani Government Services
          </h2>
          <p className="mt-2 text-slate-400">
            Get verified answers about passport, CNIC, driving licence, domicile,
            and more — in English, Roman Urdu, or Urdu.
          </p>
        </section>

        {/* Feature badges */}
        <div className="flex flex-wrap justify-center gap-2">
          <FeatureBadge icon="🎤" label="Voice Input" />
          <FeatureBadge icon="🗣️" label="Urdu Support" />
          <FeatureBadge icon="📄" label="PDF Checklist" />
          <FeatureBadge icon="🏢" label="Office Locator" />
          <FeatureBadge icon="💰" label="Fee Calculator" />
        </div>

        {/* Chat input */}
        <ChatBox onAsk={handleAsk} loading={loading} examples={EXAMPLE_QUERIES} />

        {/* Error */}
        {error && (
          <div className="glass-card rounded-xl border border-red-500/20 p-4 text-red-400 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div className="glass-card space-y-4 rounded-xl p-6 animate-pulse">
            <div className="h-6 w-3/4 rounded bg-white/10" />
            <div className="h-4 w-full rounded bg-white/10" />
            <div className="h-4 w-5/6 rounded bg-white/10" />
            <div className="h-4 w-2/3 rounded bg-white/10" />
            <div className="mt-4 h-32 rounded-lg bg-white/5" />
          </div>
        )}

        {/* Warnings */}
        {response?.warnings && response.warnings.length > 0 && (
          <WarningBanner
            warnings={response.warnings}
            contactInfo={response.contact_info}
          />
        )}

        {/* Answer */}
        {response && !loading && (
          <AnswerCard data={response} query={currentQuery} />
        )}
      </div>
    </div>
  );
}

function FeatureBadge({ icon, label }: { icon: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400">
      <span>{icon}</span>
      {label}
    </span>
  );
}
