"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@hiresense.ai");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      router.replace("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-ink-950 flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 mb-3">
            <span className="h-3 w-3 rounded-full bg-teal-accent" />
            <span className="font-display font-bold text-2xl text-white tracking-tight">HireSense AI</span>
          </div>
          <p className="text-sm text-slate-400">Explainable candidate screening — recommendations, not decisions.</p>
        </div>

        <div className="bg-white rounded-xl shadow-card p-8">
          <h1 className="font-display font-semibold text-lg text-ink-900 mb-1">Sign in</h1>
          <p className="text-sm text-slate-500 mb-6">Use your HireSense AI account to continue.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-teal-accent focus:ring-1 focus:ring-teal-accent outline-none"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-teal-accent focus:ring-1 focus:ring-teal-accent outline-none"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-ink-950 text-white text-sm font-semibold py-2.5 hover:bg-ink-900 transition-colors disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-xs text-slate-500 space-y-1">
            <p className="font-medium text-slate-600 mb-1">Demo accounts (seeded via `python -m app.seed`):</p>
            <p>admin@hiresense.ai / Admin123!  — Administrator</p>
            <p>hr@hiresense.ai / HrStaff123!  — HR Staff</p>
            <p>manager@hiresense.ai / Manager123!  — Hiring Manager</p>
          </div>
        </div>
      </div>
    </div>
  );
}
