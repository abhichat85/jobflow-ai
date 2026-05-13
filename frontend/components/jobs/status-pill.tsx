const COLORS: Record<string, string> = {
  discovered: "bg-gray-100 text-gray-700",
  parsed: "bg-blue-50 text-blue-700",
  scored: "bg-blue-100 text-blue-800",
  pending_review: "bg-yellow-100 text-yellow-800",
  approved: "bg-purple-100 text-purple-800",
  applying: "bg-purple-200 text-purple-900",
  applied: "bg-green-100 text-green-800",
  skipped: "bg-gray-50 text-gray-500",
  failed: "bg-red-100 text-red-800",
};

export function StatusPill({ status }: { status: string }) {
  const cls = COLORS[status] || "bg-gray-100 text-gray-700";
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${cls}`}>
      {status.replace("_", " ")}
    </span>
  );
}
