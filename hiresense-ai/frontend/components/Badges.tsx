const LABEL_STYLES: Record<string, string> = {
  "Highly Suitable": "bg-emerald-50 text-emerald-700 border-emerald-200",
  "Suitable": "bg-teal-50 text-teal-700 border-teal-200",
  "Potential Fit": "bg-amber-50 text-amber-700 border-amber-200",
  "Needs Review": "bg-slate-100 text-slate-600 border-slate-300",
  "Not Recommended": "bg-rose-50 text-rose-700 border-rose-200",
};

export function ScoreBadge({ score, label }: { score: number; label: string }) {
  const style = LABEL_STYLES[label] || LABEL_STYLES["Needs Review"];
  return (
    <div className="flex items-center gap-2">
      <span className="font-mono text-lg font-semibold text-ink-900">{score.toFixed(1)}</span>
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${style}`}>{label}</span>
    </div>
  );
}

const STATUS_STYLES: Record<string, string> = {
  applied: "bg-slate-100 text-slate-600",
  screened: "bg-sky-50 text-sky-700",
  advanced: "bg-emerald-50 text-emerald-700",
  needs_review: "bg-amber-50 text-amber-700",
  rejected: "bg-rose-50 text-rose-700",
  hired: "bg-teal-50 text-teal-800",
};

export function StatusPill({ status }: { status: string }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.applied;
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${style}`}>
      {status.replace("_", " ")}
    </span>
  );
}
