"use client";

import { CATEGORIES, PROVINCES, IMPORTANCE_LEVELS } from "@/types/watch";
import type { Filters } from "@/types/watch";

interface FilterPanelProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <SelectFilter
        label="Category"
        value={filters.category}
        options={CATEGORIES as unknown as string[]}
        onChange={(v) => onChange({ ...filters, category: v })}
      />
      <SelectFilter
        label="Province"
        value={filters.province}
        options={PROVINCES as unknown as string[]}
        onChange={(v) => onChange({ ...filters, province: v })}
      />
      <SelectFilter
        label="Importance"
        value={filters.importance}
        options={IMPORTANCE_LEVELS as unknown as string[]}
        onChange={(v) => onChange({ ...filters, importance: v })}
      />

      {(filters.category !== "All" ||
        filters.province !== "All" ||
        filters.importance !== "All") && (
        <button
          onClick={() =>
            onChange({ category: "All", province: "All", importance: "All" })
          }
          className="rounded-full bg-white/5 px-3 py-1.5 text-xs text-slate-400 transition hover:bg-white/10 ring-1 ring-white/10"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}

function SelectFilter({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: readonly string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-1.5">
      <label className="text-xs font-medium text-slate-500">{label}:</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-slate-300
                   focus:border-pakgreen/50 focus:outline-none"
      >
        {options.map((opt) => (
          <option key={opt} value={opt} className="bg-[#0a1a0f]">
            {opt === "All" ? `All ${label}s` : formatLabel(opt)}
          </option>
        ))}
      </select>
    </div>
  );
}

function formatLabel(s: string): string {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
