"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

const PROCESSING_STEPS = [
  "Reading your sources…",
  "Extracting experiences, projects, and skills…",
  "Synthesizing your positioning and career narrative…",
  "Generating 5 resume variant angles…",
  "Saving to your profile…",
];

export function ProfileIngestWizard() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [linkedinText, setLinkedinText] = useState("");
  const [resumeText, setResumeText] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [writingSamples, setWritingSamples] = useState<string[]>([""]);
  const [additionalContext, setAdditionalContext] = useState("");
  const [activeStep, setActiveStep] = useState(0);
  const [result, setResult] = useState<any>(null);

  const ingest = useMutation({
    mutationFn: (data: any) => api.ingestProfile(data),
    onMutate: () => {
      setResult(null);
      setActiveStep(0);
      // Advance the visible step every ~6 seconds for UX
      const id = setInterval(() => {
        setActiveStep((s) => Math.min(s + 1, PROCESSING_STEPS.length - 1));
      }, 6000);
      return { intervalId: id };
    },
    onSuccess: (data, _vars, ctx) => {
      if (ctx?.intervalId) clearInterval(ctx.intervalId);
      setActiveStep(PROCESSING_STEPS.length - 1);
      setResult(data);
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      queryClient.invalidateQueries({ queryKey: ["experiences"] });
      queryClient.invalidateQueries({ queryKey: ["variants"] });
      toast.success("Profile ingested successfully");
    },
    onError: (_err, _vars, ctx: any) => {
      if (ctx?.intervalId) clearInterval(ctx.intervalId);
      toast.error("Ingestion failed — check the backend logs");
    },
  });

  const hasAnyInput =
    linkedinText.trim() ||
    resumeText.trim() ||
    githubUrl.trim() ||
    websiteUrl.trim() ||
    writingSamples.some((s) => s.trim()) ||
    additionalContext.trim();

  const handleSubmit = () => {
    ingest.mutate({
      linkedin_text: linkedinText.trim() || undefined,
      resume_text: resumeText.trim() || undefined,
      github_url: githubUrl.trim() || undefined,
      website_url: websiteUrl.trim() || undefined,
      writing_samples: writingSamples.filter((s) => s.trim()).length > 0
        ? writingSamples.filter((s) => s.trim())
        : undefined,
      additional_context: additionalContext.trim() || undefined,
    });
  };

  const addWritingSample = () => setWritingSamples([...writingSamples, ""]);
  const removeWritingSample = (i: number) =>
    setWritingSamples(writingSamples.filter((_, idx) => idx !== i));
  const updateWritingSample = (i: number, value: string) => {
    const next = [...writingSamples];
    next[i] = value;
    setWritingSamples(next);
  };

  // Processing state
  if (ingest.isPending) {
    return (
      <Card className="p-8 max-w-2xl">
        <h2 className="text-xl font-semibold mb-2">Processing your profile</h2>
        <p className="text-sm text-gray-500 mb-6">
          This takes about a minute. We are running two AI agents — extraction then synthesis.
        </p>
        <div className="space-y-3">
          {PROCESSING_STEPS.map((step, i) => (
            <div key={i} className="flex items-center gap-3">
              <div
                className={`w-2 h-2 rounded-full ${
                  i < activeStep
                    ? "bg-green-500"
                    : i === activeStep
                    ? "bg-blue-500 animate-pulse"
                    : "bg-gray-300"
                }`}
              />
              <span
                className={`text-sm ${
                  i <= activeStep ? "text-gray-900" : "text-gray-400"
                }`}
              >
                {step}
              </span>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  // Result state
  if (result) {
    return (
      <div className="max-w-3xl space-y-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Profile Ingested</h2>
            <Badge variant="outline" className="bg-green-50 text-green-700">
              Success
            </Badge>
          </div>

          <section className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase mb-2">
              Positioning Statement
            </h3>
            <p className="text-base">{result.positioning_statement}</p>
          </section>

          <Separator className="my-4" />

          <section className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase mb-2">
              Career Narrative
            </h3>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {result.career_narrative}
            </p>
          </section>

          <Separator className="my-4" />

          {result.differentiators && result.differentiators.length > 0 && (
            <section className="mb-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase mb-2">
                Differentiators
              </h3>
              <ul className="text-sm space-y-1 list-disc pl-5">
                {result.differentiators.map((d: string, i: number) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </section>
          )}

          {result.target_roles && result.target_roles.length > 0 && (
            <section className="mb-6">
              <h3 className="text-sm font-medium text-gray-500 uppercase mb-2">
                Target Roles
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.target_roles.map((r: string) => (
                  <Badge key={r} variant="secondary">
                    {r}
                  </Badge>
                ))}
              </div>
            </section>
          )}

          {result.ats_keywords && result.ats_keywords.length > 0 && (
            <section>
              <h3 className="text-sm font-medium text-gray-500 uppercase mb-2">
                ATS Keywords ({result.ats_keywords.length})
              </h3>
              <div className="flex flex-wrap gap-1">
                {result.ats_keywords.map((k: string) => (
                  <Badge key={k} variant="outline" className="text-xs">
                    {k}
                  </Badge>
                ))}
              </div>
            </section>
          )}
        </Card>

        <div className="flex gap-3">
          <Button onClick={() => router.push("/profile")}>
            View Full Profile
          </Button>
          <Button variant="outline" onClick={() => { setResult(null); }}>
            Re-ingest
          </Button>
        </div>
      </div>
    );
  }

  // Form state
  return (
    <div className="max-w-3xl space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>Tip:</strong> Paste as much as you have. The more raw material you provide,
          the richer your synthesized profile will be. You can ingest now and edit fields later
          on the profile page.
        </p>
      </div>

      <Card className="p-5 space-y-3">
        <div>
          <label className="text-sm font-medium">LinkedIn Profile</label>
          <p className="text-xs text-gray-500 mb-2">
            Open your LinkedIn page → Ctrl/Cmd+A → Ctrl/Cmd+C → paste here.
          </p>
        </div>
        <Textarea
          placeholder="Paste your full LinkedIn profile text here..."
          value={linkedinText}
          onChange={(e) => setLinkedinText(e.target.value)}
          rows={8}
        />
      </Card>

      <Card className="p-5 space-y-3">
        <div>
          <label className="text-sm font-medium">Resume</label>
          <p className="text-xs text-gray-500 mb-2">
            Paste your resume text. PDF copy/paste usually works.
          </p>
        </div>
        <Textarea
          placeholder="Paste your resume content here..."
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
          rows={10}
        />
      </Card>

      <Card className="p-5 space-y-3">
        <div>
          <label className="text-sm font-medium">URLs (we will scrape these)</label>
          <p className="text-xs text-gray-500 mb-2">
            GitHub profile and personal website. Optional.
          </p>
        </div>
        <Input
          placeholder="https://github.com/yourusername"
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
        />
        <Input
          placeholder="https://yourwebsite.com"
          value={websiteUrl}
          onChange={(e) => setWebsiteUrl(e.target.value)}
        />
      </Card>

      <Card className="p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <label className="text-sm font-medium">Writing Samples</label>
            <p className="text-xs text-gray-500">
              Blog posts, essays, or anything that shows how you think.
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={addWritingSample}>
            + Add Sample
          </Button>
        </div>
        {writingSamples.map((sample, i) => (
          <div key={i} className="space-y-1">
            <Textarea
              placeholder={`Writing sample ${i + 1}...`}
              value={sample}
              onChange={(e) => updateWritingSample(i, e.target.value)}
              rows={4}
            />
            {writingSamples.length > 1 && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => removeWritingSample(i)}
                className="text-xs text-red-600 hover:text-red-700"
              >
                Remove
              </Button>
            )}
          </div>
        ))}
      </Card>

      <Card className="p-5 space-y-3">
        <div>
          <label className="text-sm font-medium">Additional Context</label>
          <p className="text-xs text-gray-500 mb-2">
            Career goals, interests, side projects not on LinkedIn, anything else.
          </p>
        </div>
        <Textarea
          placeholder="Tell us anything else that should shape your positioning..."
          value={additionalContext}
          onChange={(e) => setAdditionalContext(e.target.value)}
          rows={5}
        />
      </Card>

      <div className="sticky bottom-0 bg-white border-t -mx-8 px-8 py-4 flex justify-between items-center">
        <p className="text-sm text-gray-500">
          Two AI agents will process this. Takes ~60 seconds.
        </p>
        <Button onClick={handleSubmit} disabled={!hasAnyInput} size="lg">
          Process & Save Profile
        </Button>
      </div>
    </div>
  );
}
