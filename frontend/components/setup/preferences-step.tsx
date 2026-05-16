"use client";
import { useState } from "react";
import { TagInput } from "@/components/ui/tag-input";
import { JobPreferences, updatePreferences } from "@/lib/api";

const ROLE_SUGGESTIONS = [
  "Product Manager", "Senior PM", "Lead PM", "Head of Product",
  "Director of Product", "VP of Product", "Principal PM",
  "Software Engineer", "Senior Software Engineer", "Staff Engineer",
];

const SENIORITY_OPTIONS = ["Entry", "Mid", "Senior", "Lead", "Director+"];
const REMOTE_OPTIONS = [
  { value: "any", label: "Any" },
  { value: "remote", label: "Remote only" },
  { value: "hybrid", label: "Hybrid" },
  { value: "onsite", label: "On-site" },
] as const;

interface PreferencesStepProps {
  initial: JobPreferences;
  onComplete: (prefs: JobPreferences) => void;
}

export function PreferencesStep({ initial, onComplete }: PreferencesStepProps) {
  const [jobTitles, setJobTitles] = useState<string[]>(initial.job_titles);
  const [locations, setLocations] = useState<string[]>(initial.locations);
  const [remotePreference, setRemotePreference] = useState(
    initial.remote_preference
  );
  const [seniorityLevels, setSeniorityLevels] = useState<string[]>(
    initial.seniority_levels
  );
  const [minSalary, setMinSalary] = useState<string>(
    initial.min_salary ? String(initial.min_salary) : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchPreview = () => {
    const parts: string[] = [];
    if (jobTitles.length > 0) parts.push(jobTitles.join(" / "));
    if (remotePreference !== "any")
      parts.push(
        remotePreference.charAt(0).toUpperCase() + remotePreference.slice(1)
      );
    if (locations.length > 0) parts.push(locations.join(", "));
    if (seniorityLevels.length > 0) parts.push(seniorityLevels.join(", "));
    return parts.length > 0 ? parts.join(" · ") : "Add roles above to see preview";
  };

  const handleNext = async () => {
    if (jobTitles.length === 0) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updatePreferences({
        job_titles: jobTitles,
        locations,
        remote_preference: remotePreference,
        seniority_levels: seniorityLevels,
        min_salary: minSalary ? parseInt(minSalary, 10) : null,
      });
      onComplete(updated);
    } catch (e) {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">What are you looking for?</h2>
        <p className="mt-1 text-sm text-gray-500">
          Describe your ideal role — we'll build the search for you.
        </p>
      </div>

      {/* Job titles */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Job Titles / Roles
        </label>
        <TagInput
          tags={jobTitles}
          onChange={setJobTitles}
          placeholder="e.g. Product Manager (press Enter to add)"
          suggestions={ROLE_SUGGESTIONS}
        />
        {jobTitles.length === 0 && (
          <p className="text-xs text-red-500">Add at least one role to continue</p>
        )}
      </div>

      {/* Location + remote */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Locations</label>
          <TagInput
            tags={locations}
            onChange={setLocations}
            placeholder="e.g. United States"
          />
        </div>
        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">
            Work Arrangement
          </label>
          <div className="space-y-1.5">
            {REMOTE_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className="flex cursor-pointer items-center gap-2 text-sm"
              >
                <input
                  type="radio"
                  name="remote"
                  value={opt.value}
                  checked={remotePreference === opt.value}
                  onChange={() => setRemotePreference(opt.value)}
                  className="h-3.5 w-3.5 text-blue-600"
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Seniority */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Seniority Level
        </label>
        <div className="flex flex-wrap gap-2">
          {SENIORITY_OPTIONS.map((level) => {
            const active = seniorityLevels.includes(level);
            return (
              <button
                key={level}
                type="button"
                onClick={() =>
                  setSeniorityLevels(
                    active
                      ? seniorityLevels.filter((l) => l !== level)
                      : [...seniorityLevels, level]
                  )
                }
                className={`rounded-full border px-4 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "border-blue-500 bg-blue-100 text-blue-800"
                    : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                {level}
              </button>
            );
          })}
        </div>
      </div>

      {/* Min salary */}
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">
          Minimum Salary{" "}
          <span className="font-normal text-gray-400">(optional)</span>
        </label>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">$</span>
          <input
            type="number"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value)}
            placeholder="e.g. 130000"
            className="w-40 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-500">/ year</span>
        </div>
      </div>

      {/* Search preview */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
          🔍 Search Preview
        </p>
        <p className="mt-1 text-sm italic text-blue-800">{searchPreview()}</p>
        <p className="mt-1 text-xs text-blue-500">
          LinkedIn search URL will be constructed automatically
        </p>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex justify-end">
        <button
          onClick={handleNext}
          disabled={jobTitles.length === 0 || saving}
          className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? "Saving…" : "Next: Connect LinkedIn →"}
        </button>
      </div>
    </div>
  );
}
