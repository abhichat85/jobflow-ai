"use client";
import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { getPreferences, JobPreferences } from "@/lib/api";
import { PreferencesStep } from "@/components/setup/preferences-step";
import { LinkedInAuthStep } from "@/components/setup/linkedin-auth-step";
import { ReadyStep } from "@/components/setup/ready-step";

const STEP_LABELS = ["Job Preferences", "Connect LinkedIn", "Ready"];

function StepIndicator({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-0 mb-10">
      {STEP_LABELS.map((label, i) => {
        const stepNum = i + 1;
        const done = stepNum < current;
        const active = stepNum === current;
        return (
          <div key={label} className="flex items-center flex-1 last:flex-none">
            <div className="flex items-center gap-2 shrink-0">
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold ${
                  done
                    ? "bg-green-500 text-white"
                    : active
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {done ? "✓" : stepNum}
              </div>
              <span
                className={`text-sm font-medium ${
                  active
                    ? "text-blue-600"
                    : done
                    ? "text-green-600"
                    : "text-gray-400"
                }`}
              >
                {label}
              </span>
            </div>
            {i < STEP_LABELS.length - 1 && (
              <div
                className={`mx-3 h-0.5 flex-1 ${
                  done ? "bg-green-400" : "bg-gray-200"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function SetupContent() {
  const searchParams = useSearchParams();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [prefs, setPrefs] = useState<JobPreferences | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPreferences()
      .then((p) => {
        setPrefs(p);
        // Honor ?step=2 param (for re-auth flow from expired session)
        const stepParam = searchParams.get("step");
        if (stepParam === "2") setStep(2);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [searchParams]);

  const searchPreview = () => {
    if (!prefs) return "";
    const parts: string[] = [];
    if (prefs.job_titles.length > 0) parts.push(prefs.job_titles.join(" / "));
    if (prefs.remote_preference !== "any") parts.push(prefs.remote_preference);
    if (prefs.locations.length > 0) parts.push(prefs.locations[0]);
    return parts.join(" · ");
  };

  if (loading || !prefs) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-gray-500">Loading…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-start justify-center py-16 px-4">
      <div className="w-full max-w-xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-900">JobFlow AI</h1>
          <p className="mt-2 text-gray-500">Let's set up your job search</p>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
          <StepIndicator current={step} />

          {step === 1 && (
            <PreferencesStep
              initial={prefs}
              onComplete={(updated) => {
                setPrefs(updated);
                setStep(2);
              }}
            />
          )}

          {step === 2 && <LinkedInAuthStep onComplete={() => setStep(3)} />}

          {step === 3 && <ReadyStep searchPreview={searchPreview()} />}
        </div>
      </div>
    </div>
  );
}

export default function SetupPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-sm text-gray-500">Loading…</p>
        </div>
      }
    >
      <SetupContent />
    </Suspense>
  );
}
