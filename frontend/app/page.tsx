"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import Link from "next/link";

export default function DashboardPage() {
  const { data: stats } = useQuery({ queryKey: ["stats"], queryFn: api.getStats });
  const { data: pipeline } = useQuery({ queryKey: ["pipeline"], queryFn: api.getPipeline });
  const { data: followUps } = useQuery({ queryKey: ["follow-ups"], queryFn: api.getFollowUps });
  const { data: interviews } = useQuery({ queryKey: ["interviews"], queryFn: api.getInterviews });

  const upcomingInterviews = interviews?.filter((i: any) => i.status === "scheduled") || [];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      <div className="grid grid-cols-4 gap-4 mb-8">
        <div className="border rounded-lg p-4">
          <p className="text-sm text-gray-500">Total Jobs</p>
          <p className="text-3xl font-bold">{stats?.total_jobs || 0}</p>
        </div>
        <div className="border rounded-lg p-4">
          <p className="text-sm text-gray-500">Applied</p>
          <p className="text-3xl font-bold">{stats?.applied || 0}</p>
        </div>
        <div className="border rounded-lg p-4">
          <p className="text-sm text-gray-500">Avg Score</p>
          <p className="text-3xl font-bold">{stats?.avg_score || 0}</p>
        </div>
        <div className="border rounded-lg p-4">
          <p className="text-sm text-gray-500">Follow-ups Due</p>
          <p className="text-3xl font-bold">{followUps?.length || 0}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="border rounded-lg p-4">
          <h2 className="font-semibold mb-3">Pipeline</h2>
          {pipeline && (
            <div className="space-y-2">
              {Object.entries(pipeline).map(([status, count]) => (
                <div key={status} className="flex justify-between text-sm">
                  <span className="capitalize">{status}</span>
                  <span className="font-mono">{count as number}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border rounded-lg p-4">
          <h2 className="font-semibold mb-3">Upcoming Interviews</h2>
          {upcomingInterviews.length === 0 ? (
            <p className="text-sm text-gray-500">No interviews scheduled</p>
          ) : (
            upcomingInterviews.map((int: any) => (
              <div key={int.id} className="text-sm py-1 border-b last:border-0">
                <p className="font-medium">{int.company_name}</p>
                <p className="text-gray-500">{int.interview_stage}</p>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="mt-6 flex gap-3">
        <Link href="/jobs" className="text-sm text-blue-600 hover:underline">
          Add jobs &rarr;
        </Link>
        <Link href="/crm" className="text-sm text-blue-600 hover:underline">
          View pipeline &rarr;
        </Link>
      </div>
    </div>
  );
}
