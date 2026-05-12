"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export default function OutreachPage() {
  const { data: contacts } = useQuery({
    queryKey: ["contacts"],
    queryFn: api.getContacts,
  });
  const { data: outreach } = useQuery({
    queryKey: ["outreach"],
    queryFn: api.getOutreach,
  });
  const { data: followUps } = useQuery({
    queryKey: ["follow-ups"],
    queryFn: api.getFollowUps,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Outreach</h1>

      {followUps && followUps.length > 0 && (
        <div className="mb-6 border border-yellow-200 bg-yellow-50 rounded-lg p-4">
          <h2 className="font-semibold mb-2">Follow-ups Due ({followUps.length})</h2>
          {followUps.map((fu: any) => (
            <div key={fu.id} className="text-sm py-1">
              {fu.message_type} — {fu.channel}
            </div>
          ))}
        </div>
      )}

      <h2 className="text-lg font-semibold mb-3">Contacts ({contacts?.length || 0})</h2>
      <div className="border rounded-lg overflow-hidden mb-6">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-3">Name</th>
              <th className="text-left p-3">Title</th>
              <th className="text-left p-3">Company</th>
              <th className="text-left p-3">Strength</th>
            </tr>
          </thead>
          <tbody>
            {contacts?.map((c: any) => (
              <tr key={c.id} className="border-t">
                <td className="p-3">{c.name}</td>
                <td className="p-3">{c.title || "—"}</td>
                <td className="p-3">{c.company_name || "—"}</td>
                <td className="p-3"><Badge variant="outline">{c.relationship_strength}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h2 className="text-lg font-semibold mb-3">Messages ({outreach?.length || 0})</h2>
      <div className="space-y-2">
        {outreach?.map((o: any) => (
          <div key={o.id} className="border rounded p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm font-medium">{o.channel} — {o.message_type}</span>
              <Badge>{o.status}</Badge>
            </div>
            <p className="text-sm text-gray-600 line-clamp-2">{o.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
