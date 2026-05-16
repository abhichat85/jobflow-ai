"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { getPreferences, JobPreferences } from "@/lib/api";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/profile", label: "Profile", icon: "👤" },
  { href: "/jobs", label: "Jobs", icon: "💼" },
  { href: "/outreach", label: "Outreach", icon: "📨" },
  { href: "/crm", label: "CRM", icon: "📋" },
  { href: "/interviews", label: "Interviews", icon: "🎯" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

// Pages that should never trigger the setup redirect
const SETUP_EXEMPT = ["/setup", "/profile/ingest"];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [prefs, setPrefs] = useState<JobPreferences | null>(null);

  useEffect(() => {
    getPreferences()
      .then((p) => {
        setPrefs(p);
        // Redirect to setup if preferences not configured yet
        if (
          p.job_titles.length === 0 &&
          !SETUP_EXEMPT.some((exempt) => pathname.startsWith(exempt))
        ) {
          router.push("/setup");
        }
      })
      .catch(() => {
        // Backend not ready yet — fail silently
      });
  }, [pathname, router]);

  const sessionExpired = prefs?.linkedin_auth_status === "expired";

  return (
    <aside className="w-64 border-r bg-gray-50 min-h-screen p-4 flex flex-col">
      <div className="mb-8">
        <h1 className="text-xl font-bold">JobFlow AI</h1>
        <p className="text-sm text-gray-500">Job Search Agent</p>
      </div>
      <nav className="space-y-1 flex-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium",
              pathname === item.href
                ? "bg-gray-900 text-white"
                : "text-gray-700 hover:bg-gray-200"
            )}
          >
            <span>{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Persistent amber banner when LinkedIn session expired */}
      {sessionExpired && (
        <Link
          href="/setup?step=2"
          className="mt-4 block rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-700 hover:bg-amber-100"
        >
          ⚠️ LinkedIn session expired —{" "}
          <span className="font-semibold underline">Reconnect →</span>
        </Link>
      )}

      <div className="mt-4 pt-4 border-t">
        <Link
          href="/profile/ingest"
          className="block w-full text-center bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-medium rounded-md px-3 py-2 hover:opacity-90"
        >
          ✨ Ingest Profile
        </Link>
      </div>
    </aside>
  );
}
