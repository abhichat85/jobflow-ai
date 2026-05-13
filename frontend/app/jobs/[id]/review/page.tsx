"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getApplyPreview,
  submitApplication,
  getApplyStatus,
  skipApplication,
} from "@/lib/api";

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [preview, setPreview] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [taskId, setTaskId] = useState<string | null>(null);

  useEffect(() => {
    getApplyPreview(Number(id)).then(setPreview).catch(console.error);
  }, [id]);

  // Poll status once submission is enqueued
  useEffect(() => {
    if (!taskId) return;
    const t = setInterval(async () => {
      const s = await getApplyStatus(Number(id));
      setStatus(s);
      if (s.application_status === "applied" || s.application_status === "failed") {
        clearInterval(t);
      }
    }, 2000);
    return () => clearInterval(t);
  }, [taskId, id]);

  if (!preview) return <div className="p-8">Loading…</div>;

  const updateField = (k: string, v: string) =>
    setPreview({ ...preview, form_data: { ...preview.form_data, [k]: v } });

  const submit = async () => {
    setSubmitting(true);
    try {
      const r = await submitApplication(Number(id), preview.form_data);
      setTaskId(r.task_id);
    } finally {
      setSubmitting(false);
    }
  };

  const skip = async () => {
    await skipApplication(Number(id));
    router.push("/jobs");
  };

  const fd = preview.form_data;
  return (
    <div className="max-w-3xl space-y-8 p-2">
      <header>
        <h1 className="text-2xl font-semibold">{preview.role_title} @ {preview.company_name}</h1>
        <p className="text-sm text-gray-600">
          Fit score: {preview.fit_score} · ATS: {preview.ats_type}
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Application fields</h2>
        {["name", "email", "phone", "linkedin_url"].map((k) => (
          <div key={k}>
            <label className="text-sm font-medium capitalize">{k.replace("_", " ")}</label>
            <input
              value={fd[k] || ""}
              onChange={(e) => updateField(k, e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
        ))}
        <div>
          <label className="text-sm font-medium">Resume PDF path</label>
          <input
            value={fd.resume_pdf_path || ""}
            onChange={(e) => updateField("resume_pdf_path", e.target.value)}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono"
          />
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-medium">Cover letter</h2>
        <textarea
          value={fd.cover_letter_text || ""}
          onChange={(e) => updateField("cover_letter_text", e.target.value)}
          rows={12}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </section>

      <div className="flex gap-3">
        <button
          onClick={submit}
          disabled={submitting || !!taskId}
          className="rounded-md bg-blue-600 px-6 py-2 text-white disabled:opacity-50"
        >
          {submitting ? "Submitting…" : taskId ? "Submitted" : "Approve & Submit"}
        </button>
        <button
          onClick={skip}
          className="rounded-md border border-gray-300 px-6 py-2"
        >
          Skip
        </button>
      </div>

      {status && (
        <div className="rounded-md border border-gray-200 p-4">
          <p className="text-sm">Status: <strong>{status.application_status}</strong></p>
          {status.attempt?.confirmation_text && (
            <p className="mt-2 text-sm text-gray-700">{status.attempt.confirmation_text}</p>
          )}
          {status.attempt?.error_message && (
            <p className="mt-2 text-sm text-red-600">{status.attempt.error_message}</p>
          )}
        </div>
      )}
    </div>
  );
}
