"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScoreBreakdown } from "@/components/jobs/score-breakdown";
import { toast } from "sonner";

export default function JobDetailPage() {
  const { id } = useParams();
  const jobId = Number(id);
  const queryClient = useQueryClient();

  const { data: job, isLoading } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.getJob(jobId),
  });

  const { data: assets } = useQuery({
    queryKey: ["assets", jobId],
    queryFn: () => api.getJobAssets(jobId),
  });

  const scoreMutation = useMutation({
    mutationFn: () => api.scoreJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      toast.success("Job scored");
    },
    onError: () => toast.error("Scoring failed"),
  });

  const generateMutation = useMutation({
    mutationFn: () => api.generateAssets(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assets", jobId] });
      queryClient.invalidateQueries({ queryKey: ["job", jobId] });
      toast.success("Assets generated");
    },
    onError: () => toast.error("Generation failed"),
  });

  if (isLoading) return <p>Loading...</p>;
  if (!job) return <p>Job not found</p>;

  const latestScore = job.scores?.[job.scores.length - 1];

  return (
    <div className="max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{job.role_title || "Untitled Role"}</h1>
          <p className="text-gray-500">{job.company_name}</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={() => scoreMutation.mutate()}
            disabled={scoreMutation.isPending}
            variant="outline"
          >
            {scoreMutation.isPending ? "Scoring..." : "Score Job"}
          </Button>
          <Button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
          >
            {generateMutation.isPending ? "Generating..." : "Generate Assets"}
          </Button>
        </div>
      </div>

      {latestScore && (
        <div className="mb-6 border rounded-lg p-4">
          <h2 className="font-semibold mb-3">Score Breakdown</h2>
          <ScoreBreakdown score={latestScore} />
        </div>
      )}

      {assets && assets.length > 0 && (
        <div className="mb-6 border rounded-lg p-4">
          <h2 className="font-semibold mb-3">Generated Assets</h2>
          {assets.map((asset: any) => (
            <div key={asset.id} className="space-y-3">
              <div>
                <h3 className="text-sm font-medium text-gray-500">Tailored Summary</h3>
                <p className="text-sm">{asset.tailored_summary}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">Cover Letter</h3>
                <p className="text-sm whitespace-pre-wrap">{asset.cover_letter}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">LinkedIn Message</h3>
                <p className="text-sm whitespace-pre-wrap">{asset.linkedin_message}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500">Email</h3>
                <p className="text-sm whitespace-pre-wrap">{asset.email_message}</p>
              </div>
              <Badge>{asset.status}</Badge>
            </div>
          ))}
        </div>
      )}

      <div className="border rounded-lg p-4">
        <h2 className="font-semibold mb-3">Job Description</h2>
        <p className="text-sm whitespace-pre-wrap text-gray-700">
          {job.job_description || "No description available."}
        </p>
      </div>
    </div>
  );
}
