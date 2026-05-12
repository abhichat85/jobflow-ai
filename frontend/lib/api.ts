const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Profile
  getProfile: () => fetchApi<any>("/api/profile"),
  updateProfile: (data: any) =>
    fetchApi<any>("/api/profile", { method: "PUT", body: JSON.stringify(data) }),
  getExperiences: () => fetchApi<any[]>("/api/profile/experiences"),
  createExperience: (data: any) =>
    fetchApi<any>("/api/profile/experiences", { method: "POST", body: JSON.stringify(data) }),
  getSkills: () => fetchApi<any[]>("/api/profile/skills"),
  getResumeVariants: () => fetchApi<any[]>("/api/profile/resume-variants"),

  // Jobs
  getJobs: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return fetchApi<any[]>(`/api/jobs${qs}`);
  },
  getJob: (id: number) => fetchApi<any>(`/api/jobs/${id}`),
  createJob: (data: any) =>
    fetchApi<any>("/api/jobs", { method: "POST", body: JSON.stringify(data) }),
  updateJob: (id: number, data: any) =>
    fetchApi<any>(`/api/jobs/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  scoreJob: (id: number) =>
    fetchApi<any>(`/api/jobs/${id}/score`, { method: "POST" }),
  generateAssets: (id: number) =>
    fetchApi<any>(`/api/jobs/${id}/generate-assets`, { method: "POST" }),
  getJobAssets: (id: number) => fetchApi<any[]>(`/api/jobs/${id}/assets`),
  approveAsset: (jobId: number, assetId: number) =>
    fetchApi<any>(`/api/jobs/${jobId}/assets/${assetId}/approve`, { method: "POST" }),

  // CRM
  getPipeline: () => fetchApi<any>("/api/crm/pipeline"),
  getStats: () => fetchApi<any>("/api/crm/stats"),

  // Outreach
  getContacts: () => fetchApi<any[]>("/api/contacts"),
  getOutreach: () => fetchApi<any[]>("/api/outreach"),
  getFollowUps: () => fetchApi<any[]>("/api/outreach/follow-ups"),

  // Interviews
  getInterviews: () => fetchApi<any[]>("/api/interviews"),
  createInterview: (data: any) =>
    fetchApi<any>("/api/interviews", { method: "POST", body: JSON.stringify(data) }),
  getInterviewPrep: (id: number) => fetchApi<any>(`/api/interviews/${id}/prep`),
};
