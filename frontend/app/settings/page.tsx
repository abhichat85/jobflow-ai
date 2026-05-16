"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ThresholdSlider } from "@/components/settings/threshold-slider";
import {
  AppSettings,
  getSettings,
  updateSettings,
  runDiscoveryNow,
  getPreferences,
  JobPreferences,
  disconnectLinkedIn,
} from "@/lib/api";

function LinkedInCard({
  prefs,
  onDisconnect,
}: {
  prefs: JobPreferences;
  onDisconnect: () => void;
}) {
  const searchSummary = [
    ...prefs.job_titles.slice(0, 2),
    prefs.remote_preference !== "any" ? prefs.remote_preference : null,
    prefs.locations[0] ?? null,
  ]
    .filter(Boolean)
    .join(" · ");

  const handleDisconnect = async () => {
    await disconnectLinkedIn();
    onDisconnect();
  };

  if (prefs.linkedin_auth_status === "disconnected") {
    return (
      <div className="rounded-lg border border-dashed border-gray-300 p-4 text-sm text-gray-500">
        <p className="font-medium text-gray-700">LinkedIn not connected</p>
        <p className="mt-1">
          Set up LinkedIn discovery to start finding jobs automatically.
        </p>
        <Link
          href="/setup"
          className="mt-3 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Set Up LinkedIn →
        </Link>
      </div>
    );
  }

  if (prefs.linkedin_auth_status === "expired") {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm">
        <p className="font-semibold text-amber-800">
          ⚠️ Session expired — discovery is paused
        </p>
        {searchSummary && (
          <p className="mt-1 text-amber-700">Searching for: {searchSummary}</p>
        )}
        <Link
          href="/setup?step=2"
          className="mt-3 inline-block rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700"
        >
          Reconnect →
        </Link>
      </div>
    );
  }

  // Connected
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm">
      <div className="flex items-center justify-between">
        <span className="font-medium text-gray-700">LinkedIn Discovery</span>
        <span className="text-green-600 font-medium">✅ Connected</span>
      </div>
      {searchSummary && (
        <p className="mt-2 text-gray-500">Searching for: {searchSummary}</p>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        <Link
          href="/setup"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          Edit Preferences
        </Link>
        <Link
          href="/setup?step=2"
          className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
        >
          Reconnect
        </Link>
        <button
          onClick={handleDisconnect}
          className="rounded-md border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
        >
          Disconnect
        </button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [s, setS] = useState<AppSettings | null>(null);
  const [prefs, setPrefs] = useState<JobPreferences | null>(null);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    getSettings().then(setS).catch(console.error);
    getPreferences().then(setPrefs).catch(console.error);
  }, []);

  if (!s) return <div className="p-8">Loading…</div>;

  const patch = async (p: Partial<AppSettings> & { linkedin_cookie?: string }) => {
    const updated = await updateSettings(p);
    setS(updated);
    setMsg("Saved");
    setTimeout(() => setMsg(null), 2000);
  };

  const runNow = async () => {
    setRunning(true);
    try {
      await runDiscoveryNow();
      setMsg("Discovery started — refresh in a few seconds");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-10 p-2">
      <header>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-gray-600">
          Configure discovery, scoring, and auto-apply.
        </p>
        {msg && <p className="mt-2 text-xs text-green-600">{msg}</p>}
      </header>

      <section className="space-y-4">
        <h2 className="text-lg font-medium">Discovery</h2>
        {prefs ? (
          <LinkedInCard
            prefs={prefs}
            onDisconnect={() =>
              setPrefs((p) =>
                p ? { ...p, linkedin_auth_status: "disconnected" } : p
              )
            }
          />
        ) : (
          <p className="text-sm text-gray-400">Loading…</p>
        )}
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={s.discovery_enabled}
            onChange={(e) => patch({ discovery_enabled: e.target.checked })}
          />
          Discovery enabled (runs every {s.discovery_interval_hours}h)
        </label>
        <button
          onClick={runNow}
          disabled={running}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {running ? "Running…" : "Run discovery now"}
        </button>
        <p className="text-xs text-gray-500">
          Last run:{" "}
          {s.discovery_last_run_at
            ? `${new Date(s.discovery_last_run_at).toLocaleString()} — ${
                s.discovery_last_count ?? 0
              } new jobs`
            : "never"}
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-medium">Scoring</h2>
        <ThresholdSlider
          label="Review threshold"
          value={s.auto_review_threshold}
          onChange={(v) => patch({ auto_review_threshold: v })}
          hint="Jobs scoring this or higher land in your Review queue"
        />
        <ThresholdSlider
          label="Auto-apply threshold (Phase 2)"
          value={s.auto_apply_threshold}
          onChange={(v) => patch({ auto_apply_threshold: v })}
          hint="Reserved for future semi-automated apply"
        />
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-medium">Apply</h2>
        <div>
          <label className="text-sm font-medium">Cover letter tone</label>
          <select
            value={s.cover_letter_tone}
            onChange={(e) => patch({ cover_letter_tone: e.target.value })}
            className="mt-1 block rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="professional">Professional</option>
            <option value="conversational">Conversational</option>
            <option value="direct">Direct</option>
          </select>
        </div>
      </section>
    </div>
  );
}
