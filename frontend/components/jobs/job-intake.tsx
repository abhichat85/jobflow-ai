"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";

export function JobIntake() {
  const [jobUrl, setJobUrl] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const queryClient = useQueryClient();

  const createJob = useMutation({
    mutationFn: (data: any) => api.createJob(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setJobUrl("");
      setJobDescription("");
      toast.success("Job added");
    },
  });

  const handleSubmit = () => {
    if (!jobDescription && !jobUrl) return;
    createJob.mutate({
      job_url: jobUrl || undefined,
      job_description: jobDescription || undefined,
      source: "manual",
    });
  };

  return (
    <div className="border rounded-lg p-4 mb-6 space-y-3">
      <h2 className="font-semibold">Add Job</h2>
      <Input
        placeholder="Job URL (optional)"
        value={jobUrl}
        onChange={(e) => setJobUrl(e.target.value)}
      />
      <Textarea
        placeholder="Paste job description here..."
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        rows={6}
      />
      <Button onClick={handleSubmit} disabled={createJob.isPending}>
        {createJob.isPending ? "Adding..." : "Add Job"}
      </Button>
    </div>
  );
}
