import { ProfileIngestWizard } from "@/components/profile/profile-ingest-wizard";

export default function ProfileIngestPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Ingest Your Profile</h1>
      <p className="text-gray-500 mb-8 max-w-2xl">
        Paste your LinkedIn, resume, GitHub, and any other sources. Two AI agents will extract
        your experiences and skills, then synthesize your positioning, career narrative, and 5
        resume variant angles. This drives everything downstream — job scoring, resume tailoring,
        outreach, interview prep.
      </p>
      <ProfileIngestWizard />
    </div>
  );
}
