"use client";

import { useState } from "react";
import { JobIntake } from "@/components/jobs/job-intake";
import { JobsTable } from "@/components/jobs/jobs-table";

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string>("pending_review");

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Jobs</h1>
      <JobIntake />
      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
          Status
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-gray-300 px-2 py-1 text-sm"
        >
          <option value="all">All</option>
          <option value="pending_review">Pending review</option>
          <option value="applied">Applied</option>
          <option value="skipped">Skipped</option>
          <option value="failed">Failed</option>
        </select>
      </div>
      <JobsTable statusFilter={statusFilter} />
    </div>
  );
}
