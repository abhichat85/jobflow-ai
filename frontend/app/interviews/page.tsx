"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

export default function InterviewsPage() {
  const { data: interviews } = useQuery({
    queryKey: ["interviews"],
    queryFn: api.getInterviews,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Interviews</h1>
      {(!interviews || interviews.length === 0) ? (
        <p className="text-gray-500">No interviews scheduled yet.</p>
      ) : (
        <div className="space-y-3">
          {interviews.map((int: any) => (
            <div key={int.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-medium">{int.company_name} — {int.interview_stage}</p>
                  <p className="text-sm text-gray-500">
                    {int.interviewer_name && `with ${int.interviewer_name}`}
                    {int.interview_date && ` on ${new Date(int.interview_date).toLocaleDateString()}`}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Badge>{int.status}</Badge>
                  <Badge variant="outline">{int.outcome}</Badge>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
