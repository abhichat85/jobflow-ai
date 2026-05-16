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
  ingestProfile: (data: {
    linkedin_text?: string;
    resume_text?: string;
    github_url?: string;
    website_url?: string;
    writing_samples?: string[];
    additional_context?: string;
  }) => fetchApi<any>("/api/profile/ingest", { method: "POST", body: JSON.stringify(data) }),

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

// ----- Discovery -----
export async function getDiscoveryStatus() {
  const r = await fetch(`${API_BASE}/api/discovery/status`);
  if (!r.ok) throw new Error("Failed to load discovery status");
  return r.json();
}

export async function runDiscoveryNow() {
  const r = await fetch(`${API_BASE}/api/discovery/run`, { method: "POST" });
  if (!r.ok) throw new Error("Failed to start discovery");
  return r.json();
}

// ----- Settings -----
export interface AppSettings {
  id: number;
  linkedin_cookie_present: boolean;
  linkedin_search_url: string | null;
  yc_filters: Record<string, unknown> | null;
  discovery_enabled: boolean;
  discovery_interval_hours: number;
  discovery_last_run_at: string | null;
  discovery_last_count: number | null;
  auto_review_threshold: number;
  auto_apply_threshold: number;
  daily_apply_cap: number;
  default_resume_variant: string | null;
  cover_letter_tone: string;
}

export async function getSettings(): Promise<AppSettings> {
  const r = await fetch(`${API_BASE}/api/settings`);
  if (!r.ok) throw new Error("Failed to load settings");
  return r.json();
}

export async function updateSettings(
  patch: Partial<AppSettings> & { linkedin_cookie?: string }
): Promise<AppSettings> {
  const r = await fetch(`${API_BASE}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!r.ok) throw new Error("Failed to update settings");
  return r.json();
}

// ----- Apply -----
export async function getApplyPreview(jobId: number) {
  const r = await fetch(`${API_BASE}/api/apply/${jobId}/preview`);
  if (!r.ok) throw new Error("Failed to load apply preview");
  return r.json();
}

export async function submitApplication(jobId: number, formData: Record<string, unknown>) {
  const r = await fetch(`${API_BASE}/api/apply/${jobId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });
  if (!r.ok) throw new Error("Failed to submit application");
  return r.json();
}

export async function getApplyStatus(jobId: number) {
  const r = await fetch(`${API_BASE}/api/apply/${jobId}/status`);
  if (!r.ok) throw new Error("Failed to load apply status");
  return r.json();
}

export async function skipApplication(jobId: number) {
  const r = await fetch(`${API_BASE}/api/apply/${jobId}/skip`, { method: "POST" });
  if (!r.ok) throw new Error("Failed to skip application");
  return r.json();
}

// ----- Preferences -----
export interface JobPreferences {
  job_titles: string[];
  locations: string[];
  remote_preference: "any" | "remote" | "hybrid" | "onsite";
  seniority_levels: string[];
  company_stage: "any" | "startup" | "growth" | "public";
  min_salary: number | null;
  linkedin_auth_status: "disconnected" | "connected" | "expired";
  linkedin_search_urls: string[];
  linkedin_search_url: string | null;
}

export async function getPreferences(): Promise<JobPreferences> {
  const r = await fetch(`${API_BASE}/api/settings/preferences`);
  if (!r.ok) throw new Error("Failed to load preferences");
  return r.json();
}

export async function updatePreferences(
  patch: Partial<Omit<JobPreferences, "linkedin_auth_status" | "linkedin_search_urls" | "linkedin_search_url">>
): Promise<JobPreferences> {
  const r = await fetch(`${API_BASE}/api/settings/preferences`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!r.ok) throw new Error("Failed to update preferences");
  return r.json();
}

// ----- LinkedIn Auth -----
export async function startLinkedInAuth(): Promise<{ session_id: string }> {
  const r = await fetch(`${API_BASE}/api/settings/linkedin/start-auth`, {
    method: "POST",
  });
  if (!r.ok) throw new Error("Failed to start LinkedIn auth");
  return r.json();
}

export async function getLinkedInAuthStatus(
  sessionId: string
): Promise<{ status: "waiting" | "connected" | "timeout" }> {
  const r = await fetch(
    `${API_BASE}/api/settings/linkedin/auth-status/${sessionId}`
  );
  if (!r.ok) throw new Error("Failed to get auth status");
  return r.json();
}

export async function disconnectLinkedIn(): Promise<void> {
  const r = await fetch(`${API_BASE}/api/settings/linkedin/disconnect`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error("Failed to disconnect LinkedIn");
}
