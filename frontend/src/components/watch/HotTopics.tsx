"use client";

import type { TopicDigest } from "@/types/watch";
import { ConfidenceBadge } from "./ConfidenceBadge";

interface HotTopicsProps {
  topics: TopicDigest[];
  loading?: boolean;
  onSelectTopic: (query: string) => void;
}

export function HotTopics({ topics, loading, onSelectTopic }: HotTopicsProps) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 animate-pulse">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-36 glass-card rounded-lg"
          />
        ))}
      </div>
    );
  }

  if (topics.length === 0) return null;

  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-lg font-bold text-white">Hot Topics</h3>
        <span className="text-xs text-slate-500">
          Pre-computed — refreshed automatically
        </span>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {topics.map((topic) => (
          <TopicCard key={topic.topic} topic={topic} onClick={onSelectTopic} />
        ))}
      </div>
    </section>
  );
}

function TopicCard({
  topic,
  onClick,
}: {
  topic: TopicDigest;
  onClick: (query: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onClick(topic.query)}
      className="glass-card group flex h-full flex-col items-start gap-2 rounded-xl p-4 text-left
                 transition hover:border-pakgreen/30 focus:outline-none focus:ring-2 focus:ring-pakgreen/30"
    >
      <div className="flex w-full items-center justify-between gap-2">
        <h4 className="text-sm font-semibold text-slate-200 group-hover:text-pakgreen transition-colors">
          {topic.topic}
        </h4>
        <ConfidenceBadge confidence={topic.confidence} />
      </div>

      <p className="line-clamp-3 flex-1 text-sm text-slate-400">
        {topic.answer || "No update available."}
      </p>

      <div className="flex w-full items-center justify-between text-xs text-slate-600">
        {topic.effective_date && (
          <span>Effective: {topic.effective_date}</span>
        )}
        {topic.generated_at && (
          <span className="ml-auto">
            Updated{" "}
            {new Date(topic.generated_at).toLocaleDateString("en-PK", {
              month: "short",
              day: "numeric",
            })}
          </span>
        )}
      </div>
    </button>
  );
}
