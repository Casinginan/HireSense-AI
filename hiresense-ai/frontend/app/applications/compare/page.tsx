"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import Shell from "@/components/Shell";
import { ScoreBadge } from "@/components/Badges";
import { apiRequest, ApiError } from "@/lib/api";
import type { Application } from "@/lib/types";

export default function ComparePage() {
  return (
    <Suspense fallback={null}>
      <CompareContent />
    </Suspense>
  );
}

function CompareContent() {
  const searchParams = useSearchParams();
  const ids = searchParams.get("ids") || "";
  const [applications, setApplications] = useState<Application[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ids) return;
    apiRequest<Application[]>(`/applications/compare?application_ids=${ids}`)
      .then(setApplications)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load comparison."));
  }, [ids]);

  const categories = ["skills", "experience", "education", "certifications", "projects", "semantic_similarity"];
  const categoryLabels: Record<string, string> = {
    skills: "Skills",
    experience: "Experience",
    education: "Education",
    certifications: "Certifications",
    projects: "Projects",
    semantic_similarity: "Semantic similarity",
  };

  return (
    <Shell>
      <h1 className="font-display text-2xl font-bold text-ink-900 mb-1">Candidate comparison</h1>
      <p className="text-sm text-slate-500 mb-6">Side-by-side view to support your final recommendation.</p>

      {error && <div className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">{error}</div>}
      {!applications && !error && <p className="text-sm text-slate-500">Loading…</p>}

      {applications && (
        <div className="bg-white rounded-xl shadow-card overflow-x-auto">
          <table className="w-full text-sm min-w-[600px]">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="text-left font-medium text-slate-500 px-5 py-4 w-40">Candidate</th>
                {applications.map((app) => (
                  <th key={app.id} className="text-left font-medium px-5 py-4">
                    <Link href={`/applications/${app.id}`} className="text-ink-900 hover:text-teal-accent">
                      {app.candidate?.full_name}
                    </Link>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="px-5 py-3 text-slate-500">Overall score</td>
                {applications.map((app) => (
                  <td key={app.id} className="px-5 py-3">
                    {app.latest_score ? (
                      <ScoreBadge score={app.latest_score.overall_score} label={app.latest_score.suitability_label} />
                    ) : (
                      "—"
                    )}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-5 py-3 text-slate-500">Experience</td>
                {applications.map((app) => (
                  <td key={app.id} className="px-5 py-3 font-mono">{app.candidate?.total_experience_years} yrs</td>
                ))}
              </tr>
              <tr>
                <td className="px-5 py-3 text-slate-500">Education</td>
                {applications.map((app) => (
                  <td key={app.id} className="px-5 py-3 capitalize">{app.candidate?.highest_education_level}</td>
                ))}
              </tr>
              {categories.map((cat) => (
                <tr key={cat}>
                  <td className="px-5 py-3 text-slate-500">{categoryLabels[cat]}</td>
                  {applications.map((app) => (
                    <td key={app.id} className="px-5 py-3 font-mono">
                      {app.latest_score?.category_breakdown[cat] ?? "—"}
                    </td>
                  ))}
                </tr>
              ))}
              <tr>
                <td className="px-5 py-3 text-slate-500 align-top">Skills</td>
                {applications.map((app) => (
                  <td key={app.id} className="px-5 py-3">
                    <div className="flex flex-wrap gap-1">
                      {app.candidate?.skills.map((s) => (
                        <span key={s} className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">{s}</span>
                      ))}
                    </div>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </Shell>
  );
}
