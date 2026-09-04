interface VerificationBadgeProps {
  confidence: "high" | "medium" | "low";
}

const CONFIDENCE_STYLES = {
  high: {
    bg: "bg-green-500/10",
    text: "text-green-400",
    border: "border-green-500/20",
    label: "High Confidence",
    description: "Cross-verified by multiple AI models",
  },
  medium: {
    bg: "bg-yellow-500/10",
    text: "text-yellow-400",
    border: "border-yellow-500/20",
    label: "Medium Confidence",
    description: "Partially verified — some details may need confirmation",
  },
  low: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/20",
    label: "Low Confidence",
    description: "Limited verification — please verify with official source",
  },
};

export function VerificationBadge({ confidence }: VerificationBadgeProps) {
  const style = CONFIDENCE_STYLES[confidence];

  return (
    <div
      className={`flex-shrink-0 rounded-lg border px-3 py-2 ${style.bg} ${style.border}`}
      title={style.description}
    >
      <p className={`text-xs font-bold ${style.text}`}>{style.label}</p>
      <p className={`text-xs ${style.text} opacity-80`}>{style.description}</p>
    </div>
  );
}
