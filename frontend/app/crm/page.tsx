"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function CRMPage() {
  const { data: pipeline } = useQuery({
    queryKey: ["pipeline"],
    queryFn: api.getPipeline,
  });
  const { data: stats } = useQuery({
    queryKey: ["stats"],
    queryFn: api.getStats,
  });

  const stages = [
    { key: "discovered", label: "Discovered", color: "bg-gray-200" },
    { key: "scored", label: "Scored", color: "bg-blue-200" },
    { key: "ready", label: "Ready", color: "bg-green-200" },
    { key: "applied", label: "Applied", color: "bg-purple-200" },
    { key: "rejected", label: "Rejected", color: "bg-red-200" },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">CRM Pipeline</h1>

      {stats && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-500">Total Jobs</p>
            <p className="text-2xl font-bold">{stats.total_jobs}</p>
          </div>
          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-500">Applied</p>
            <p className="text-2xl font-bold">{stats.applied}</p>
          </div>
          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-500">Avg Score</p>
            <p className="text-2xl font-bold">{stats.avg_score}</p>
          </div>
        </div>
      )}

      <div className="flex gap-4">
        {stages.map((stage) => (
          <div key={stage.key} className="flex-1">
            <div className={`${stage.color} rounded-t-lg px-3 py-2 font-medium text-sm`}>
              {stage.label}
            </div>
            <div className="border border-t-0 rounded-b-lg p-3 min-h-[200px]">
              <p className="text-3xl font-bold text-center">
                {pipeline?.[stage.key] || 0}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
