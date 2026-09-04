interface RequirementListProps {
  items: string[];
}

export function RequirementList({ items }: RequirementListProps) {
  return (
    <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-400">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ol>
  );
}
