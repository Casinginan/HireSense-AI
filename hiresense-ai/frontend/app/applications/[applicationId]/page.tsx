"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Shell from "@/components/Shell";
import { ScoreBadge, StatusPill } from "@/components/Badges";
import { apiRequest, ApiError, getCurrentUser } from "@/lib/api";
import type { Application } from "@/lib/types";

const CATEGORY_LABELS: Record<string, string> = {
  skills: "Skills match",
  experience: "Experience",
  education: "Education",
  certifications: "Certifications",
  projects: "Projects",
  semantic_similarity: "Semantic similarity",
};

export default function ApplicationDetailPage() {
  const params = useParams();
  const applicationId = params.applicationId as string;
  const user = getCurrentUser();

  const [application, setApplication] = useState<Application | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [submittingAction, setSubmittingAction] = useState<string | null>(null);
  const [decisionMessage, setDecisionMessage] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const app = await apiRequest<Application>(`/applications/${applicationId}`);
        setApplication(app);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not load this application.");
      }
    })();
  }, [applicationId]);

  async function recordDecision(action: "advance" | "reject" | "defer" | "hire") {
    setSubmittingAction(action);
    setDecisionMessage(null);
    try {
      await apiRequest(`/applications/${applicationId}/decision`, {
        method: "POST",
        body: { action, note: note || null },
      });
      setDecisionMessage(`Recorded: ${action}. This decision and the AI recommendation at this time are now in the audit log.`);
      setNote("");
    } catch (err) {
      setDecisionMessage(err instanceof ApiError ? err.message : "Could not record this decision.");
    } finally {
      setSubmittingAction(null);
    }
  }

  const canDecide = user && ["admin", "hr_staff", "hiring_manager"].includes(user.role);

  return (
    <Shell>
      {error && <div className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700 mb-6">{error}</div>}

      {!application && !error && <p className="text-sm text-slate-500">Loading…</p>}

      {application?.candidate && (
        <div className="mb-6">
          <h1 className="font-display text-2xl font-bold text-ink-900">{application.candidate.full_name}</h1>
          <p className="text-sm text-slate-500 mt-1">
            {application.candidate.email || "No email on file"} · {application.candidate.total_experience_years} yrs experience ·{" "}
            {application.candidate.highest_education_level}
          </p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {application.candidate.skills.map((s) => (
              <span key={s} className="text-xs px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">{s}</span>
            ))}
          </div>
        </div>
      )}

      {application?.latest_score && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-xl shadow-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h1 className="font-display text-xl font-bold text-ink-900">AI Score Explanation</h1>
                <ScoreBadge score={application.latest_score.overall_score} label={application.latest_score.suitability_label} />
              </div>
              <p className="text-sm text-slate-600 mb-5">{application.latest_score.recommendation_text}</p>

              <h2 className="text-sm font-semibold text-ink-900 mb-3">Score breakdown</h2>
              <div className="space-y-2 mb-5">
                {Object.entries(application.latest_score.category_breakdown).map(([key, value]) => (
                  <div key={key} className="flex items-center gap-3">
                    <span className="w-40 text-sm text-slate-600 shrink-0">{CATEGORY_LABELS[key] || key}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div className="h-full bg-teal-accent rounded-full" style={{ width: `${value}%` }} />
                    </div>
                    <span className="w-12 text-right font-mono text-xs text-ink-900">{value}</span>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4 mb-5">
                <div>
                  <h3 className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-2">Matched skills</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {application.latest_score.matched_skills.map((s) => (
                      <span key={s} className="text-xs px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700">{s}</span>
                    ))}
                    {application.latest_score.matched_skills.length === 0 && <span className="text-xs text-slate-400">None</span>}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-semibold text-rose-700 uppercase tracking-wide mb-2">Missing skills</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {application.latest_score.missing_skills.map((s) => (
                      <span key={s} className="text-xs px-2 py-0.5 rounded-md bg-rose-50 text-rose-700">{s}</span>
                    ))}
                    {application.latest_score.missing_skills.length === 0 && <span className="text-xs text-slate-400">None</span>}
                  </div>
                </div>
              </div>

              <h2 className="text-sm font-semibold text-ink-900 mb-2">Top contributing factors</h2>
              <ul className="space-y-1.5">
                {application.latest_score.explanation_factors.map((f, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <span
                      className={
                        f.direction === "positive"
                          ? "text-emerald-600"
                          : f.direction === "negative"
                          ? "text-rose-600"
                          : "text-slate-400"
                      }
                    >
                      {f.direction === "positive" ? "▲" : f.direction === "negative" ? "▼" : "•"}
                    </span>
                    <span className="text-slate-700">{f.factor}{f.value !== null ? ` — ${f.value}` : ""}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-5 pt-4 border-t border-slate-100 text-xs text-slate-400 flex justify-between">
                <span>Model version: {application.latest_score.model_version}</span>
                <span>Scored: {new Date(application.latest_score.scored_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-card p-6">
              <h2 className="font-display font-semibold text-ink-900 mb-1">Human decision</h2>
              <p className="text-xs text-slate-500 mb-4">
                The AI score above is a recommendation only. Your decision — and the recommendation shown at the time — is permanently recorded.
              </p>

              {!canDecide && (
                <p className="text-xs text-slate-400">Your role does not have permission to record hiring decisions.</p>
              )}

              {canDecide && (
                <>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Optional note explaining your reasoning…"
                    rows={3}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm mb-3 focus:border-teal-accent focus:ring-1 focus:ring-teal-accent outline-none"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <DecisionButton label="Advance" color="emerald" onClick={() => recordDecision("advance")} loading={submittingAction === "advance"} />
                    <DecisionButton label="Reject" color="rose" onClick={() => recordDecision("reject")} loading={submittingAction === "reject"} />
                    <DecisionButton label="Defer / needs review" color="amber" onClick={() => recordDecision("defer")} loading={submittingAction === "defer"} />
                    <DecisionButton label="Mark hired" color="teal" onClick={() => recordDecision("hire")} loading={submittingAction === "hire"} />
                  </div>
                  {decisionMessage && <p className="text-xs text-slate-600 mt-3">{decisionMessage}</p>}
                </>
              )}
            </div>

            <div className="bg-white rounded-xl shadow-card p-6">
              <h2 className="font-display font-semibold text-ink-900 mb-1">Status</h2>
              <StatusPill status={application.status} />
            </div>
          </div>
        </div>
      )}
    </Shell>
  );
}

function DecisionButton({
  label,
  color,
  onClick,
  loading,
}: {
  label: string;
  color: "emerald" | "rose" | "amber" | "teal";
  onClick: () => void;
  loading: boolean;
}) {
  const styles: Record<string, string> = {
    emerald: "bg-emerald-50 text-emerald-700 hover:bg-emerald-100",
    rose: "bg-rose-50 text-rose-700 hover:bg-rose-100",
    amber: "bg-amber-50 text-amber-700 hover:bg-amber-100",
    teal: "bg-teal-50 text-teal-800 hover:bg-teal-100",
  };
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`text-sm font-semibold rounded-lg px-3 py-2 transition-colors disabled:opacity-60 ${styles[color]}`}
    >
      {loading ? "Saving…" : label}
    </button>
  );
}
