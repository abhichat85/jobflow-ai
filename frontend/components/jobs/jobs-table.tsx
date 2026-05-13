"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import Link from "next/link";
import { ScoreBadge } from "@/components/jobs/score-badge";
import { StatusPill } from "@/components/jobs/status-pill";

interface Props {
  statusFilter?: string;
}

export function JobsTable({ statusFilter = "all" }: Props) {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.getJobs(),
  });

  if (isLoading) return <p>Loading...</p>;

  const filteredJobs = (jobs ?? []).filter((j: any) =>
    statusFilter === "all"
      ? true
      : (j.application_status ?? "discovered") === statusFilter
  );

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
            <th className="text-left p-3"></th>
          </tr>
        </thead>
        <tbody>
          {filteredJobs.map((job: any) => {
            const appStatus = job.application_status ?? "discovered";
            return (
              <tr key={job.id} className="border-t hover:bg-gray-50">
                <td className="p-3">
                  <Link href={`/jobs/${job.id}`} className="text-blue-600 hover:underline">
                    {job.company_name || "—"}
                  </Link>
                </td>
                <td className="p-3">{job.role_title || "—"}</td>
                <td className="p-3">
                  <ScoreBadge score={job.fit_score ?? null} />
                </td>
                <td className="p-3">
                  <StatusPill status={appStatus} />
                </td>
                <td className="p-3">{job.source || "—"}</td>
                <td className="p-3 text-gray-500">
                  {new Date(job.created_at).toLocaleDateString()}
                </td>
                <td className="p-3">
                  {appStatus === "pending_review" && (
                    <Link
                      href={`/jobs/${job.id}/review`}
                      className="rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700"
                    >
                      Review
                    </Link>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {filteredJobs.length === 0 && (
        <p className="p-6 text-center text-gray-500">No jobs match this filter.</p>
      )}
    </div>
  );
}
