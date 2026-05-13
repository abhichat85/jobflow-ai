interface Props {
  score: number | null;
}

export function ScoreBadge({ score }: Props) {
  if (score == null) {
    return <span className="text-xs text-gray-400">—</span>;
  }
  const color =
    score >= 80 ? "bg-green-100 text-green-800" :
    score >= 65 ? "bg-yellow-100 text-yellow-800" :
                  "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>
      {score}
    </span>
  );
}
