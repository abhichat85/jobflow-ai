"use client";
import { useState } from "react";

interface Props {
  initialPresent: boolean;
  onSave: (cookie: string) => Promise<void>;
}

export function LinkedInCookieInput({ initialPresent, onSave }: Props) {
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(value);
      setValue("");
      setSavedAt(new Date());
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">LinkedIn session cookie (li_at)</span>
        {initialPresent && (
          <span className="text-xs rounded-full bg-green-100 text-green-700 px-2 py-0.5">
            saved
          </span>
        )}
      </div>
      <input
        type="password"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={initialPresent ? "•••••••• (set — paste new to replace)" : "Paste your li_at cookie value"}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
      />
      <p className="text-xs text-gray-500">
        Get this from DevTools → Application → Cookies → linkedin.com → li_at. Encrypted at rest.
      </p>
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={saving || !value}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          {saving ? "Saving…" : "Save cookie"}
        </button>
        {initialPresent && (
          <button
            onClick={() => onSave("")}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm"
          >
            Clear
          </button>
        )}
      </div>
      {savedAt && (
        <p className="text-xs text-green-600">
          Saved at {savedAt.toLocaleTimeString()}
        </p>
      )}
    </div>
  );
}
