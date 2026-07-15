"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Shell from "@/components/Shell";
import { ScoreBadge, StatusPill } from "@/components/Badges";
import { apiRequest, ApiError } from "@/lib/api";
import type { Application, Job } from "@/lib/types";

export default function JobDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.jobId as string;

  const [job, setJob] = useState<Job | null>(null);
  const [applications, setApplications] = useState<Application[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);

  const loadJob = useCallback(async () => {
    try {
      const j = await apiRequest<Job>(`/jobs/${jobId}`);
      setJob(j);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load job.");
    }
  }, [jobId]);

  const loadApplications = useCallback(async () => {
    try {
      const apps = await apiRequest<Application[]>(`/jobs/${jobId}/applications?sort=score_desc`);
      setApplications(apps);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load applications.");
    }
  }, [jobId]);

  useEffect(() => {
    loadJob();
    loadApplications();
  }, [loadJob, loadApplications]);

  async function handlePublish() {
    try {
      await apiRequest(`/jobs/${jobId}/publish`, { method: "POST" });
      loadJob();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not publish job.");
    }
  }

  async function handleClose() {
    try {
      await apiRequest(`/jobs/${jobId}/close`, { method: "POST" });
      loadJob();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not close job.");
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setUploadError(null);
    setUploading(true);
    const formData = new FormData();
    Array.from(files).forEach((f) => formData.append("files", f));
    try {
      await apiRequest(`/jobs/${jobId}/resumes`, { method: "POST", body: formData, isForm: true });
      await loadApplications();
      await loadJob();
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Could not upload resumes.");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  function toggleSelect(id: string) {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  if (error) {
    return (
      <Shell>
        <div className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">{error}</div>
      </Shell>
    );
  }

  return (
    <Shell>
      {!job ? (
        <p className="text-sm text-slate-500">Loading job…</p>
      ) : (
        <>
          <div className="mb-6 flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="font-display text-2xl font-bold text-ink-900">{job.title}</h1>
                <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">{job.status}</span>
              </div>
              <p className="text-sm text-slate-500 mt-1">
                {job.department || "No department"} · {job.location || "No location"} · {job.min_experience_years}–{job.max_experience_years} yrs experience
              </p>
            </div>
            <div className="flex gap-2">
              {job.status === "draft" && (
                <button onClick={handlePublish} className="rounded-lg bg-ink-950 text-white text-sm font-semibold px-4 py-2 hover:bg-ink-900 transition-colors">
                  Publish
                </button>
              )}
              {job.status === "published" && (
                <button onClick={handleClose} className="rounded-lg border border-slate-300 text-slate-700 text-sm font-semibold px-4 py-2 hover:bg-slate-50 transition-colors">
                  Close job
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2 bg-white rounded-xl shadow-card p-6">
              <h2 className="font-display font-semibold text-ink-900 mb-2">Description</h2>
              <p className="text-sm text-slate-600 whitespace-pre-line">{job.description}</p>
              <h3 className="font-display font-semibold text-ink-900 mt-5 mb-2">Required skills</h3>
              <div className="flex flex-wrap gap-2 mb-3">
                {job.skills.filter((s) => s.requirement_type === "required").map((s) => (
                  <span key={s.name} className="text-xs font-medium px-2 py-1 rounded-md bg-ink-950 text-white">{s.name}</span>
                ))}
                {job.skills.filter((s) => s.requirement_type === "required").length === 0 && (
                  <span className="text-xs text-slate-400">None defined yet — required to publish.</span>
                )}
              </div>
              <h3 className="font-display font-semibold text-ink-900 mb-2">Preferred skills</h3>
              <div className="flex flex-wrap gap-2">
                {job.skills.filter((s) => s.requirement_type === "preferred").map((s) => (
                  <span key={s.name} className="text-xs font-medium px-2 py-1 rounded-md bg-slate-100 text-slate-700">{s.name}</span>
                ))}
                {job.skills.filter((s) => s.requirement_type === "preferred").length === 0 && (
                  <span className="text-xs text-slate-400">None defined.</span>
                )}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-card p-6">
              <h2 className="font-display font-semibold text-ink-900 mb-2">Upload resumes</h2>
              <p className="text-xs text-slate-500 mb-3">PDF or DOCX. Each file is parsed and scored automatically.</p>
              <label className="block">
                <span className="sr-only">Upload resumes</span>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  multiple
                  onChange={handleUpload}
                  disabled={uploading}
                  className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:bg-ink-950 file:text-white file:px-3 file:py-2 file:text-sm file:font-semibold hover:file:bg-ink-900 file:cursor-pointer cursor-pointer"
                />
              </label>
              {uploading && <p className="text-xs text-slate-500 mt-2">Uploading and scoring…</p>}
              {uploadError && <p className="text-xs text-rose-600 mt-2">{uploadError}</p>}
            </div>
          </div>

          <div className="flex items-center justify-between mb-3">
            <h2 className="font-display font-semibold text-ink-900">
              Ranked applicants {applications ? `(${applications.length})` : ""}
            </h2>
            {selected.length >= 2 && (
              <button
                onClick={() => router.push(`/applications/compare?ids=${selected.join(",")}`)}
                className="text-sm font-semibold text-teal-accent hover:underline"
              >
                Compare selected ({selected.length}) →
              </button>
            )}
          </div>

          {applications && applications.length === 0 && (
            <div className="bg-white rounded-xl shadow-card p-10 text-center">
              <p className="text-slate-600 font-medium">No applicants yet.</p>
              <p className="text-sm text-slate-500 mt-1">Upload resumes above to start screening candidates.</p>
            </div>
          )}

          {applications && applications.length > 0 && (
            <div className="bg-white rounded-xl shadow-card overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wide">
                  <tr>
                    <th className="px-4 py-3 w-8"></th>
                    <th className="text-left font-medium px-2 py-3">Candidate</th>
                    <th className="text-left font-medium px-4 py-3">Score</th>
                    <th className="text-left font-medium px-4 py-3">Status</th>
                    <th className="text-left font-medium px-4 py-3">Matched skills</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {applications.map((app) => (
                    <tr key={app.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-4">
                        <input
                          type="checkbox"
                          checked={selected.includes(app.id)}
                          onChange={() => toggleSelect(app.id)}
                          className="rounded border-slate-300"
                        />
                      </td>
                      <td className="px-2 py-4">
                        <Link href={`/applications/${app.id}`} className="font-medium text-ink-900 hover:text-teal-accent">
                          {app.candidate?.full_name}
                        </Link>
                        <p className="text-xs text-slate-400">{app.candidate?.email}</p>
                      </td>
                      <td className="px-4 py-4">
                        {app.latest_score ? (
                          <ScoreBadge score={app.latest_score.overall_score} label={app.latest_score.suitability_label} />
                        ) : (
                          <span className="text-xs text-slate-400">Pending</span>
                        )}
                      </td>
                      <td className="px-4 py-4"><StatusPill status={app.status} /></td>
                      <td className="px-4 py-4 text-xs text-slate-500">
                        {app.latest_score?.matched_skills.slice(0, 4).join(", ") || "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </Shell>
  );
}
