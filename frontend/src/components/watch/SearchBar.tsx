"use client";

import { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading: boolean;
}

const EXAMPLE_QUERIES = [
  "Latest government policy changes in Punjab",
  "What changed in NADRA rules?",
  "Petrol ke naye rates kya hain?",
  "تازہ حکومتی نوٹیفکیشنز کیا ہیں؟",
];

export function SearchBar({ onSearch, loading }: SearchBarProps) {
  const [input, setInput] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSearch(input.trim());
    }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          dir="auto"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask in English, Roman Urdu, or Urdu — e.g. petrol ke naye rates kya hain?"
          className="glow-input flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white
                     placeholder-slate-500 outline-none backdrop-blur
                     focus:border-pakgreen/50
                     disabled:opacity-50"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn-gradient rounded-xl px-6 py-3 text-sm font-medium text-white
                     disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      <div className="flex flex-wrap gap-2">
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => {
              setInput(q);
              if (!loading) onSearch(q);
            }}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400
                       hover:border-pakgreen/30 hover:text-pakgreen transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
