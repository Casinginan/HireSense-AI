"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { apiRequest, ApiError } from "@/lib/api";
import type { AuditLogEntry, ScoringWeights } from "@/lib/types";

const CATEGORY_LABELS: Record<keyof ScoringWeights, string> = {
  skills: "Skills match",
  experience: "Experience",
  education: "Education",
  certifications: "Certifications",
  projects: "Projects",
  semantic_similarity: "Semantic similarity",
};

export default function AdminPage() {
  const [weights, setWeights] = useState<ScoringWeights | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [logs, setLogs] = useState<AuditLogEntry[] | null>(null);

  useEffect(() => {
    apiRequest<ScoringWeights>("/admin/settings/scoring-weights").then(setWeights).catch((e) => setError(e.message));
    apiRequest<AuditLogEntry[]>("/admin/audit-logs?limit=50").then(setLogs).catch((e) => setError(e.message));
  }, []);

  const total = weights ? Object.values(weights).reduce((a, b) => a + b, 0) : 0;

  async function handleSave() {
    if (!weights) return;
    setSaving(true);
    setSavedMessage(null);
    setError(null);
    try {
      const updated = await apiRequest<ScoringWeights>("/admin/settings/scoring-weights", {
        method: "PUT",
        body: weights,
      });
      setWeights(updated);
      setSavedMessage("Scoring weights saved. Future scoring runs will use this configuration.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save scoring weights.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Shell>
      <h1 className="font-display text-2xl font-bold text-ink-900 mb-1">Admin</h1>
      <p className="text-sm text-slate-500 mb-6">Configure scoring weights and review the audit trail.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-card p-6">
          <h2 className="font-display font-semibold text-ink-900 mb-1">Scoring weights</h2>
          <p className="text-xs text-slate-500 mb-4">Must sum to 100%. Changes apply to future scoring runs only.</p>

          {weights && (
            <div className="space-y-4">
              {(Object.keys(weights) as (keyof ScoringWeights)[]).map((key) => (
                <div key={key} className="flex items-center gap-3">
                  <span className="w-40 text-sm text-slate-700">{CATEGORY_LABELS[key]}</span>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={weights[key]}
                    onChange={(e) => setWeights({ ...weights, [key]: Number(e.target.value) })}
                    className="w-20 rounded-lg border border-slate-300 px-2 py-1.5 text-sm text-right font-mono focus:border-teal-accent focus:ring-1 focus:ring-teal-accent outline-none"
                  />
                  <span className="text-sm text-slate-400">%</span>
                </div>
              ))}

              <div className={`text-sm font-medium ${total === 100 ? "text-emerald-600" : "text-rose-600"}`}>
                Total: {total}% {total !== 100 && "(must equal 100%)"}
              </div>

              <button
                onClick={handleSave}
                disabled={saving || total !== 100}
                className="rounded-lg bg-ink-950 text-white text-sm font-semibold px-4 py-2.5 hover:bg-ink-900 transition-colors disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save weights"}
              </button>

              {savedMessage && <p className="text-xs text-emerald-600">{savedMessage}</p>}
              {error && <p className="text-xs text-rose-600">{error}</p>}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-card p-6">
          <h2 className="font-display font-semibold text-ink-900 mb-1">Audit log</h2>
          <p className="text-xs text-slate-500 mb-4">Most recent 50 events. Entries are permanent and cannot be edited or deleted.</p>

          <div className="max-h-[420px] overflow-y-auto space-y-2">
            {logs?.map((log) => (
              <div key={log.id} className="text-xs border-b border-slate-100 pb-2">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-ink-900">{log.event_type.replace(/_/g, " ")}</span>
                  <span className="text-slate-400">{new Date(log.created_at).toLocaleString()}</span>
                </div>
                {log.entity_type && (
                  <p className="text-slate-500">
                    {log.entity_type} · {log.entity_id?.slice(0, 8)}
                  </p>
                )}
              </div>
            ))}
            {logs && logs.length === 0 && <p className="text-xs text-slate-400">No audit events yet.</p>}
          </div>
        </div>
      </div>
    </Shell>
  );
}
