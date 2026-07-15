"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Shell from "@/components/Shell";
import { apiRequest } from "@/lib/api";
import type { AnalyticsSummary } from "@/lib/types";

const FUNNEL_ORDER = ["applied", "screened", "advanced", "needs_review", "rejected", "hired"];
const FUNNEL_LABELS: Record<string, string> = {
  applied: "Applied",
  screened: "Screened",
  advanced: "Advanced",
  needs_review: "Needs Review",
  rejected: "Rejected",
  hired: "Hired",
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<AnalyticsSummary>("/admin/analytics/summary")
      .then(setSummary)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Shell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-ink-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            An at-a-glance view of your hiring pipeline. Every score below is a recommendation — final decisions are always yours.
          </p>
        </div>
        <Link
          href="/jobs/new"
          className="rounded-lg bg-ink-950 text-white text-sm font-semibold px-4 py-2.5 hover:bg-ink-900 transition-colors"
        >
          + New job posting
        </Link>
      </div>

      {error && <div className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700 mb-6">{error}</div>}

      {!summary && !error && <p className="text-sm text-slate-500">Loading analytics…</p>}

      {summary && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total jobs" value={summary.total_jobs} />
            <StatCard label="Published jobs" value={summary.published_jobs} />
            <StatCard label="Total applications" value={summary.total_applications} />
            <StatCard
              label="Average match score"
              value={summary.average_match_score !== null ? summary.average_match_score.toFixed(1) : "—"}
              hint={`${summary.scored_applications} scored`}
            />
          </div>

          <div className="bg-white rounded-xl shadow-card p-6">
            <h2 className="font-display font-semibold text-ink-900 mb-4">Hiring funnel</h2>
            <div className="space-y-3">
              {FUNNEL_ORDER.map((key) => {
                const value = summary.hiring_funnel[key] ?? 0;
                const max = Math.max(...Object.values(summary.hiring_funnel), 1);
                const width = Math.max(4, (value / max) * 100);
                return (
                  <div key={key} className="flex items-center gap-4">
                    <span className="w-28 text-sm text-slate-600 shrink-0">{FUNNEL_LABELS[key]}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden">
                      <div
                        className="h-full bg-teal-accent rounded-full transition-all"
                        style={{ width: `${width}%` }}
                      />
                    </div>
                    <span className="w-10 text-right font-mono text-sm text-ink-900">{value}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </Shell>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="bg-white rounded-xl shadow-card p-5">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="font-mono text-2xl font-semibold text-ink-900 mt-1">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
    </div>
  );
}
