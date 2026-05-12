"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

const statusColors: Record<string, string> = {
  discovered: "bg-gray-100 text-gray-800",
  scored: "bg-blue-100 text-blue-800",
  ready: "bg-green-100 text-green-800",
  applied: "bg-purple-100 text-purple-800",
  rejected: "bg-red-100 text-red-800",
  paused: "bg-yellow-100 text-yellow-800",
};

export function JobsTable() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.getJobs(),
  });

  if (isLoading) return <p>Loading...</p>;

  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="text-left p-3">Company</th>
            <th className="text-left p-3">Role</th>
            <th className="text-left p-3">Score</th>
            <th className="text-left p-3">Status</th>
            <th className="text-left p-3">Source</th>
            <th className="text-left p-3">Date</th>
          </tr>
        </thead>
        <tbody>
          {jobs?.map((job: any) => (
            <tr key={job.id} className="border-t hover:bg-gray-50">
              <td className="p-3">
                <Link href={`/jobs/${job.id}`} className="text-blue-600 hover:underline">
                  {job.company_name || "—"}
                </Link>
              </td>
              <td className="p-3">{job.role_title || "—"}</td>
              <td className="p-3 font-mono">
                {job.fit_score != null ? job.fit_score : "—"}
              </td>
              <td className="p-3">
                <Badge className={statusColors[job.status] || ""}>
                  {job.status}
                </Badge>
              </td>
              <td className="p-3">{job.source || "—"}</td>
              <td className="p-3 text-gray-500">
                {new Date(job.created_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {(!jobs || jobs.length === 0) && (
        <p className="p-6 text-center text-gray-500">No jobs yet. Add one above.</p>
      )}
    </div>
  );
}
