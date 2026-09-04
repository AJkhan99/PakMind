"use client";

import { useState, type FormEvent } from "react";
import { VoiceInput } from "./VoiceInput";

interface ChatBoxProps {
  onAsk: (question: string) => void;
  loading: boolean;
  examples: string[];
}

export function ChatBox({ onAsk, loading, examples }: ChatBoxProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = query.trim();
    if (trimmed && !loading) {
      onAsk(trimmed);
    }
  }

  function handleExample(example: string) {
    setQuery(example);
    onAsk(example);
  }

  function handleVoiceTranscript(text: string) {
    setQuery(text);
    onAsk(text);
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask PakGuide... e.g. How do I get a domicile in Rawalpindi?"
          dir="auto"
          disabled={loading}
          className="glow-input flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white
                     placeholder-slate-500 outline-none backdrop-blur
                     focus:border-pakgreen/50
                     disabled:opacity-50"
        />
        <VoiceInput onTranscript={handleVoiceTranscript} disabled={loading} />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="btn-gradient rounded-xl px-6 py-3 text-sm font-semibold text-white
                     disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>

      {/* Example queries */}
      <div className="flex flex-wrap gap-2">
        {examples.map((ex) => (
          <button
            key={ex}
            onClick={() => handleExample(ex)}
            disabled={loading}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400
                       hover:border-pakgreen/30 hover:text-pakgreen transition-colors
                       disabled:opacity-40"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
