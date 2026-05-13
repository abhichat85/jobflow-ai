"use client";
import { useEffect, useState } from "react";
import { LinkedInCookieInput } from "@/components/settings/linkedin-cookie-input";
import { ThresholdSlider } from "@/components/settings/threshold-slider";
import { AppSettings, getSettings, updateSettings, runDiscoveryNow } from "@/lib/api";

export default function SettingsPage() {
  const [s, setS] = useState<AppSettings | null>(null);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    getSettings().then(setS).catch(console.error);
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
        <p className="text-sm text-gray-600">Configure discovery, scoring, and auto-apply.</p>
        {msg && <p className="mt-2 text-xs text-green-600">{msg}</p>}
      </header>

      <section className="space-y-4">
        <h2 className="text-lg font-medium">Discovery</h2>
        <LinkedInCookieInput
          initialPresent={s.linkedin_cookie_present}
          onSave={(cookie) => patch({ linkedin_cookie: cookie })}
        />
        <div>
          <label className="text-sm font-medium">LinkedIn jobs search URL</label>
          <input
            type="url"
            defaultValue={s.linkedin_search_url || ""}
            onBlur={(e) => patch({ linkedin_search_url: e.target.value })}
            placeholder="https://www.linkedin.com/jobs/search/?keywords=AI+PM"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
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
          Last run: {s.discovery_last_run_at
            ? `${new Date(s.discovery_last_run_at).toLocaleString()} — ${s.discovery_last_count ?? 0} new jobs`
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
