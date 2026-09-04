export default function WatchLoading() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-pakgreen" />
      <p className="text-sm text-gray-500">Loading PakWatch…</p>
    </div>
  );
}
