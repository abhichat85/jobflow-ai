"use client";

interface ScoreBreakdownProps {
  score: {
    role_match: number;
    skill_match: number;
    startup_fit: number;
    ai_relevance: number;
    location_fit: number;
    speed_of_hiring: number;
    compensation_fit: number;
    total_score: number;
    decision: string;
    reasoning: string;
    resume_angle: string;
    outreach_angle: string;
  };
}

const dimensions = [
  { key: "role_match", label: "Role Match", max: 25 },
  { key: "skill_match", label: "Skill Match", max: 20 },
  { key: "startup_fit", label: "Startup Fit", max: 15 },
  { key: "ai_relevance", label: "AI Relevance", max: 15 },
  { key: "location_fit", label: "Location Fit", max: 10 },
  { key: "speed_of_hiring", label: "Speed of Hiring", max: 10 },
  { key: "compensation_fit", label: "Compensation Fit", max: 5 },
];

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <span className="text-4xl font-bold">{score.total_score}</span>
        <span className="text-lg text-gray-500">/ 100</span>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            score.decision === "apply"
              ? "bg-green-100 text-green-800"
              : score.decision === "maybe"
              ? "bg-yellow-100 text-yellow-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {score.decision.toUpperCase()}
        </span>
      </div>

      <div className="space-y-2">
        {dimensions.map((dim) => {
          const value = (score as any)[dim.key] as number;
          const pct = (value / dim.max) * 100;
          return (
            <div key={dim.key} className="flex items-center gap-3">
              <span className="w-36 text-sm text-gray-600">{dim.label}</span>
              <div className="flex-1 h-2 bg-gray-100 rounded-full">
                <div
                  className="h-2 bg-blue-600 rounded-full"
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-sm font-mono w-12 text-right">
                {value}/{dim.max}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-gray-50 rounded-md text-sm">
        <p className="font-medium mb-1">Reasoning</p>
        <p className="text-gray-600">{score.reasoning}</p>
      </div>
      <div className="flex gap-4 text-sm">
        <div>
          <span className="text-gray-500">Resume angle:</span>{" "}
          <span className="font-medium">{score.resume_angle}</span>
        </div>
        <div>
          <span className="text-gray-500">Outreach angle:</span>{" "}
          <span className="font-medium">{score.outreach_angle}</span>
        </div>
      </div>
    </div>
  );
}
