import type { GuideSource } from "@/types/guide";

interface SourceCardProps {
  source: GuideSource;
}

export function SourceCard({ source }: SourceCardProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-medium text-slate-300">
            {source.title || "Government Source"}
          </p>
          <p className="text-xs text-slate-500">{source.source_name}</p>
        </div>
        {source.url && (
          <a
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 rounded-lg bg-gradient-to-r from-pakgreen to-teal-500 px-2.5 py-1 text-xs text-white hover:shadow-lg hover:shadow-pakgreen/20 transition-all"
          >
            Visit
          </a>
        )}
      </div>
    </div>
  );
}
