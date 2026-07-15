"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Shell from "@/components/Shell";
import { apiRequest } from "@/lib/api";
import type { Job } from "@/lib/types";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600",
  published: "bg-emerald-50 text-emerald-700",
  closed: "bg-amber-50 text-amber-700",
  archived: "bg-slate-100 text-slate-400",
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<Job[]>("/jobs")
      .then(setJobs)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Shell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-ink-900">Job postings</h1>
          <p className="text-sm text-slate-500 mt-1">Manage requisitions and review AI-ranked candidates.</p>
        </div>
        <Link
          href="/jobs/new"
          className="rounded-lg bg-ink-950 text-white text-sm font-semibold px-4 py-2.5 hover:bg-ink-900 transition-colors"
        >
          + New job posting
        </Link>
      </div>

      {error && <div className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700 mb-6">{error}</div>}

      {!jobs && !error && <p className="text-sm text-slate-500">Loading jobs…</p>}

      {jobs && jobs.length === 0 && (
        <div className="bg-white rounded-xl shadow-card p-10 text-center">
          <p className="text-slate-600 font-medium">No job postings yet.</p>
          <p className="text-sm text-slate-500 mt-1">Create your first requisition to start screening candidates.</p>
        </div>
      )}

      {jobs && jobs.length > 0 && (
        <div className="bg-white rounded-xl shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wide">
              <tr>
                <th className="text-left font-medium px-5 py-3">Title</th>
                <th className="text-left font-medium px-5 py-3">Department</th>
                <th className="text-left font-medium px-5 py-3">Status</th>
                <th className="text-left font-medium px-5 py-3">Applicants</th>
                <th className="text-left font-medium px-5 py-3">Experience range</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-5 py-4">
                    <Link href={`/jobs/${job.id}`} className="font-medium text-ink-900 hover:text-teal-accent">
                      {job.title}
                    </Link>
                  </td>
                  <td className="px-5 py-4 text-slate-600">{job.department || "—"}</td>
                  <td className="px-5 py-4">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_STYLES[job.status]}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-5 py-4 font-mono text-ink-900">{job.applicant_count}</td>
                  <td className="px-5 py-4 text-slate-600">
                    {job.min_experience_years}–{job.max_experience_years} yrs
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Shell>
  );
}
