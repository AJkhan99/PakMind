"use client";

import { motion } from "framer-motion";

export default function LoadingIndicator({ label }: { label?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex flex-col items-center gap-6 py-12"
    >
      {/* Spinning gradient ring */}
      <div className="relative h-14 w-14">
        <div className="spin-ring absolute inset-0" />
        <div className="absolute inset-2 rounded-full bg-background/80" />
      </div>

      {/* Pulsing dots */}
      <div className="flex items-center gap-2">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="pulse-dot inline-block h-2 w-2 rounded-full bg-brand-green"
            style={{ animationDelay: `${i * 0.2}s` }}
          />
        ))}
      </div>

      <p className="text-sm font-medium text-slate-400 animate-pulse">
        {label || "Searching across all modules..."}
      </p>
    </motion.div>
  );
}
