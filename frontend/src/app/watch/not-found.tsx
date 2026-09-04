import Link from "next/link";

export default function WatchNotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-100 text-3xl">
        🗺️
      </div>
      <h2 className="text-2xl font-bold text-gray-900">Page not found</h2>
      <p className="max-w-md text-sm text-gray-500">
        The page you are looking for does not exist or may have been moved.
      </p>
      <Link
        href="/"
        className="rounded-lg bg-pakgreen px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-pakgreen-dark"
      >
        Back to PakMind
      </Link>
    </div>
  );
}
