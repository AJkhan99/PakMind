"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { queryWatch, getLatestUpdates, getHotTopics } from "@/lib/api";
import type { HotTopic } from "@/lib/api";
import { isUrdu } from "@/lib/smartSearch";
import type {
  QueryResponse,
  GovernmentUpdate,
  TopicDigest,
  Filters,
} from "@/types/watch";
import { SearchBar } from "@/components/watch/SearchBar";
import { FilterPanel } from "@/components/watch/FilterPanel";
import { UpdateCard } from "@/components/watch/UpdateCard";
import { SourceCard } from "@/components/watch/SourceCard";
import { ConfidenceBadge } from "@/components/watch/ConfidenceBadge";
import { HotTopics } from "@/components/watch/HotTopics";

/** Map the unified API HotTopic into the TopicDigest shape used by the UI. */
function mapHotTopicToDigest(ht: HotTopic): TopicDigest {
  return {
    topic: ht.topic,
    query: ht.query || ht.topic,
    answer: ht.answer,
    what_changed: ht.what_changed,
    who_affected: ht.who_affected,
    effective_date: ht.effective_date,
    confidence: ht.confidence,
    generated_at: ht.generated_at,
  };
}

export default function PakWatchPage() {
  const [filters, setFilters] = useState<Filters>({
    category: "All",
    province: "All",
    importance: "All",
  });
  const [latestUpdates, setLatestUpdates] = useState<GovernmentUpdate[]>([]);
  const [latestLoading, setLatestLoading] = useState(true);
  const [latestError, setLatestError] = useState<string | null>(null);

  const [aiResponse, setAiResponse] = useState<QueryResponse | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const [topics, setTopics] = useState<TopicDigest[]>([]);
  const [topicsLoading, setTopicsLoading] = useState(true);

  const loadLatest = useCallback(async () => {
    setLatestLoading(true);
    setLatestError(null);
    try {
      const data = await getLatestUpdates(
        filters.category !== "All" ? filters.category : undefined,
        filters.province !== "All" ? filters.province : undefined,
        20,
      );
      let updates = (data.updates || []) as unknown as GovernmentUpdate[];
      if (filters.importance !== "All") {
        updates = updates.filter((u) => u.importance === filters.importance);
      }
      setLatestUpdates(updates);
    } catch (err) {
      setLatestError(
        err instanceof Error ? err.message : "Failed to load updates.",
      );
    } finally {
      setLatestLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadLatest();
  }, [loadLatest]);

  useEffect(() => {
    getHotTopics()
      .then((data) =>
        setTopics((data.topics || []).map(mapHotTopicToDigest)),
      )
      .catch(() => setTopics([]))
      .finally(() => setTopicsLoading(false));
  }, []);

  async function handleSearch(query: string) {
    setAiLoading(true);
    setAiError(null);
    setAiResponse(null);

    try {
      const data = await queryWatch(query);
      // Map the unified WatchResponse into the richer QueryResponse shape
      const mapped: QueryResponse = {
        module: data.module,
        answer: data.answer,
        updates: (data.updates || []) as unknown as GovernmentUpdate[],
        sources: (data.sources || []).map((s) => ({
          title: s.title,
          url: s.url,
          source_name: s.source_name,
          published_date: null,
          last_verified: null,
        })),
        what_changed: data.what_changed,
        who_affected: data.who_affected,
        effective_date: data.effective_date,
        last_verified: null,
        confidence: data.confidence,
        warnings: data.warnings || [],
      };
      setAiResponse(mapped);
    } catch (err) {
      setAiError(
        err instanceof Error ? err.message : "An unknown error occurred.",
      );
    } finally {
      setAiLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Back to Home */}
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-pakgreen transition-colors"
      >
        <svg
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 19l-7-7 7-7"
          />
        </svg>
        Back to Home
      </Link>

      {/* Hero */}
      <section className="text-center">
        <h2 className="text-3xl font-bold gradient-text">
          Monitor Pakistani Government Updates
        </h2>
        <p className="mt-2 text-slate-400 max-w-2xl mx-auto">
          Track policy changes, notifications, regulations, and announcements
          from official government sources. Ask in English, Roman Urdu, or Urdu.
        </p>
      </section>

      {/* Hot Topics */}
      <HotTopics
        topics={topics}
        loading={topicsLoading}
        onSelectTopic={handleSearch}
      />

      {/* Search */}
      <SearchBar onSearch={handleSearch} loading={aiLoading} />

      {/* AI Error */}
      {aiError && (
        <div className="glass-card rounded-xl border border-red-500/20 p-4 text-sm text-red-400">
          <strong>Error:</strong> {aiError}
        </div>
      )}

      {/* AI Loading */}
      {aiLoading && (
        <div className="glass-card space-y-4 rounded-xl p-6 animate-pulse">
          <div className="h-5 w-3/4 rounded bg-white/10" />
          <div className="h-4 w-full rounded bg-white/10" />
          <div className="h-4 w-5/6 rounded bg-white/10" />
          <div className="h-4 w-2/3 rounded bg-white/10" />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="h-24 rounded-lg bg-white/5" />
            <div className="h-24 rounded-lg bg-white/5" />
          </div>
        </div>
      )}

      {/* AI Response */}
      {aiResponse && !aiLoading && (
        <AiResponseSection response={aiResponse} />
      )}

      {/* Divider */}
      {aiResponse && <hr className="border-white/10" />}

      {/* Latest updates header + filters */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">Latest Updates</h3>
          <button
            onClick={loadLatest}
            disabled={latestLoading}
            className="text-xs text-pakgreen hover:underline disabled:opacity-50"
          >
            {latestLoading ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        <FilterPanel filters={filters} onChange={setFilters} />
      </div>

      {/* Latest Error */}
      {latestError && (
        <div className="glass-card rounded-xl border border-red-500/20 p-4 text-sm text-red-400">
          <strong>Error:</strong> {latestError}
        </div>
      )}

      {/* Latest Loading */}
      {latestLoading && (
        <div className="grid gap-4 sm:grid-cols-2 animate-pulse">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-32 glass-card rounded-lg"
            />
          ))}
        </div>
      )}

      {/* Latest Updates Grid */}
      {!latestLoading && latestUpdates.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {latestUpdates.map((update, i) => (
            <UpdateCard key={update.id || i} update={update} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!latestLoading && latestUpdates.length === 0 && !latestError && (
        <div className="glass-card rounded-xl border-dashed p-8 text-center">
          <p className="text-slate-500">
            No updates found matching your filters.
          </p>
          <button
            onClick={() =>
              setFilters({
                category: "All",
                province: "All",
                importance: "All",
              })
            }
            className="mt-2 text-sm text-pakgreen hover:underline"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}

function AiResponseSection({ response }: { response: QueryResponse }) {
  return (
    <div className="glass-card space-y-5 rounded-xl p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">AI Analysis</h3>
        <ConfidenceBadge confidence={response.confidence} />
      </div>

      <div className="prose prose-sm max-w-none">
        <p
          dir={isUrdu(response.answer) ? "rtl" : "auto"}
          className="text-slate-300 leading-relaxed whitespace-pre-wrap"
        >
          {response.answer}
        </p>
      </div>

      {response.what_changed && (
        <div className="rounded-lg border border-pakgreen/20 bg-pakgreen/5 p-4">
          <h4 className="text-xs font-semibold uppercase text-pakgreen">
            What Changed
          </h4>
          <p dir="auto" className="mt-1 text-sm text-slate-400">
            {response.what_changed}
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
        {response.who_affected && (
          <span>
            <strong>Who is affected:</strong> {response.who_affected}
          </span>
        )}
        {response.effective_date && (
          <span>
            <strong>Effective:</strong> {response.effective_date}
          </span>
        )}
        {response.last_verified && (
          <span>
            <strong>Last verified:</strong>{" "}
            {new Date(response.last_verified).toLocaleDateString("en-PK", {
              year: "numeric",
              month: "short",
              day: "numeric",
            })}
          </span>
        )}
      </div>

      {response.warnings && response.warnings.length > 0 && (
        <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
          <h4 className="text-xs font-semibold uppercase text-amber-400">
            Warnings
          </h4>
          <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-amber-300/80">
            {response.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {response.updates && response.updates.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500">
            Referenced Updates
          </h4>
          <div className="grid gap-3 sm:grid-cols-2">
            {response.updates.map((u, i) => (
              <UpdateCard key={i} update={u} />
            ))}
          </div>
        </div>
      )}

      {response.sources && response.sources.length > 0 && (
        <div>
          <h4 className="mb-2 text-xs font-semibold uppercase text-slate-500">
            Official Sources
          </h4>
          <div className="grid gap-2 sm:grid-cols-2">
            {response.sources.map((s, i) => (
              <SourceCard key={i} source={s} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
