"use client";

interface ConfidenceBadgeProps {
  confidence: "high" | "medium" | "low";
}

const CONFIDENCE_STYLES = {
  high: {
    bg: "bg-green-500/10",
    text: "text-green-400",
    border: "border-green-500/20",
    label: "High Confidence",
  },
  medium: {
    bg: "bg-yellow-500/10",
    text: "text-yellow-400",
    border: "border-yellow-500/20",
    label: "Medium Confidence",
  },
  low: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/20",
    label: "Low Confidence",
  },
};

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const style = CONFIDENCE_STYLES[confidence] || CONFIDENCE_STYLES.medium;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${style.bg} ${style.text} ${style.border}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          confidence === "high"
            ? "bg-green-400"
            : confidence === "medium"
            ? "bg-yellow-400"
            : "bg-red-400"
        }`}
      />
      {style.label}
    </span>
  );
}
