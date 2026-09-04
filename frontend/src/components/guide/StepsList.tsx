interface StepsListProps {
  items: string[];
}

export function StepsList({ items }: StepsListProps) {
  return (
    <ol className="space-y-2">
      {items.map((step, i) => (
        <li key={i} className="flex gap-3 text-sm">
          <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-pakgreen to-teal-500 text-xs font-bold text-white">
            {i + 1}
          </span>
          <span className="pt-0.5 text-slate-400">{step}</span>
        </li>
      ))}
    </ol>
  );
}
