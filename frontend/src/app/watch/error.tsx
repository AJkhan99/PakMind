"use client";

import { useEffect } from "react";

export default function WatchError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("PakWatch error boundary:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-50 text-3xl">
        🛑
      </div>
      <h2 className="text-2xl font-bold text-gray-900">
        Something went wrong
      </h2>
      <p className="max-w-md text-sm text-gray-500">
        An unexpected error occurred while loading PakWatch. Your monitored
        updates are safe — please try again.
      </p>
      <button
        onClick={reset}
        className="rounded-lg bg-pakgreen px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-pakgreen-dark"
      >
        Try again
      </button>
    </div>
  );
}
