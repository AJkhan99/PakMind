"use client";

import { useState } from "react";
import { submitFeedback } from "@/lib/api";

interface FeedbackButtonsProps {
  query: string;
  responseSnapshot: Record<string, unknown>;
}

export function FeedbackButtons({ query, responseSnapshot }: FeedbackButtonsProps) {
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [showComment, setShowComment] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleRate(value: number) {
    setRating(value);
    if (value <= 3) {
      setShowComment(true);
    } else {
      await submit(value);
    }
  }

  async function submit(rate: number) {
    setSubmitting(true);
    try {
      await submitFeedback(query, rate, comment || undefined, responseSnapshot);
      setSubmitted(true);
    } catch {
      // Silently fail
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-green-500/20 bg-green-500/10 px-4 py-2">
        <svg className="h-4 w-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <span className="text-sm text-green-400">Thank you for your feedback!</span>
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-white/10 bg-white/5 p-4">
      <div className="flex items-center gap-2">
        <span className="text-sm text-slate-400">Was this helpful?</span>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              onClick={() => handleRate(star)}
              disabled={submitting}
              className={`text-xl transition-colors ${
                rating && star <= rating
                  ? "text-yellow-400"
                  : "text-slate-600 hover:text-yellow-300"
              }`}
            >
              ★
            </button>
          ))}
        </div>
      </div>

      {showComment && rating && (
        <div className="space-y-2">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="What was wrong or missing? (optional)"
            rows={2}
            className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-300
                       placeholder-slate-500
                       focus:border-pakgreen/50 focus:outline-none focus:ring-1 focus:ring-pakgreen/30"
          />
          <button
            onClick={() => submit(rating)}
            disabled={submitting}
            className="btn-gradient rounded-md px-4 py-1.5 text-sm font-medium text-white
                       disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit Feedback"}
          </button>
        </div>
      )}
    </div>
  );
}
