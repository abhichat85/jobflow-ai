"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { runDiscoveryNow } from "@/lib/api";

interface ReadyStepProps {
  searchPreview: string;
}

export function ReadyStep({ searchPreview }: ReadyStepProps) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const handleRunNow = async () => {
    setRunning(true);
    try {
      await runDiscoveryNow();
      setMsg("Discovery started! Redirecting to jobs…");
      setTimeout(() => router.push("/jobs"), 2000);
    } catch {
      setMsg("Failed to start discovery. You can trigger it from Settings.");
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-4 text-center">
        <div className="text-5xl">🎉</div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            JobFlow is ready to find jobs!
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Your preferences and LinkedIn session are saved.
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">LinkedIn</span>
          <span className="font-medium text-green-600">✅ Connected</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Searching for</span>
          <span className="font-medium text-gray-800 text-right max-w-[240px] truncate">
            {searchPreview}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-500">Auto-discovery</span>
          <span className="font-medium text-gray-800">Every 6 hours</span>
        </div>
      </div>

      {msg && (
        <p className="text-center text-sm text-green-600">{msg}</p>
      )}

      <div className="flex flex-col gap-3">
        <button
          onClick={handleRunNow}
          disabled={running}
          className="w-full rounded-lg bg-green-600 py-3 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
        >
          {running ? "Starting…" : "▶ Run Discovery Now"}
        </button>
        <button
          onClick={() => router.push("/settings")}
          className="w-full rounded-lg border border-gray-300 bg-white py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          View Settings
        </button>
      </div>
    </div>
  );
}
