import { JobIntake } from "@/components/jobs/job-intake";
import { JobsTable } from "@/components/jobs/jobs-table";

export default function JobsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Jobs</h1>
      <JobIntake />
      <JobsTable />
    </div>
  );
}
