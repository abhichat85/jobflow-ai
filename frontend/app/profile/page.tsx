"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useState, useEffect } from "react";
import { toast } from "sonner";

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { data: profile, isLoading } = useQuery({
    queryKey: ["profile"],
    queryFn: api.getProfile,
  });
  const { data: experiences } = useQuery({
    queryKey: ["experiences"],
    queryFn: api.getExperiences,
  });
  const { data: variants } = useQuery({
    queryKey: ["variants"],
    queryFn: api.getResumeVariants,
  });

  const [form, setForm] = useState<any>({});

  useEffect(() => {
    if (profile) setForm(profile);
  }, [profile]);

  const updateProfile = useMutation({
    mutationFn: (data: any) => api.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
      toast.success("Profile saved");
    },
  });

  if (isLoading) return <p>Loading...</p>;

  return (
    <div className="max-w-3xl space-y-8">
      <h1 className="text-2xl font-bold">Profile</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Personal Info</h2>
        <div className="grid grid-cols-2 gap-3">
          <Input placeholder="Name" value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="Email" value={form.email || ""} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <Input placeholder="Phone" value={form.phone || ""} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <Input placeholder="Location" value={form.location || ""} onChange={(e) => setForm({ ...form, location: e.target.value })} />
          <Input placeholder="LinkedIn URL" value={form.linkedin_url || ""} onChange={(e) => setForm({ ...form, linkedin_url: e.target.value })} />
          <Input placeholder="GitHub URL" value={form.github_url || ""} onChange={(e) => setForm({ ...form, github_url: e.target.value })} />
        </div>
        <Textarea
          placeholder="Positioning statement"
          value={form.positioning_statement || ""}
          onChange={(e) => setForm({ ...form, positioning_statement: e.target.value })}
          rows={3}
        />
        <Textarea
          placeholder="Bio"
          value={form.bio || ""}
          onChange={(e) => setForm({ ...form, bio: e.target.value })}
          rows={4}
        />
        <Button onClick={() => updateProfile.mutate(form)}>Save Profile</Button>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">
          Experiences ({experiences?.length || 0})
        </h2>
        {experiences?.map((exp: any) => (
          <div key={exp.id} className="border rounded p-3 mb-2">
            <p className="font-medium">{exp.role_title} at {exp.company_name}</p>
            <p className="text-sm text-gray-500">{exp.type} | {exp.is_current ? "Current" : `${exp.start_date} — ${exp.end_date}`}</p>
          </div>
        ))}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">
          Resume Variants ({variants?.length || 0})
        </h2>
        {variants?.map((v: any) => (
          <div key={v.id} className="border rounded p-3 mb-2">
            <p className="font-medium">{v.variant_name}</p>
            <p className="text-sm text-gray-500">{v.positioning_statement || "No positioning set"}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
