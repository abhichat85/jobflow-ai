"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: "📊" },
  { href: "/profile", label: "Profile", icon: "👤" },
  { href: "/jobs", label: "Jobs", icon: "💼" },
  { href: "/outreach", label: "Outreach", icon: "📨" },
  { href: "/crm", label: "CRM", icon: "📋" },
  { href: "/interviews", label: "Interviews", icon: "🎯" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r bg-gray-50 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold">JobFlow AI</h1>
        <p className="text-sm text-gray-500">Job Search Agent</p>
      </div>
      <nav className="space-y-1">
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
      <div className="mt-6 pt-6 border-t">
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
