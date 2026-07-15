"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import { apiRequest, ApiError } from "@/lib/api";
import type { Job } from "@/lib/types";

export default function NewJobPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [department, setDepartment] = useState("");
  const [location, setLocation] = useState("Remote");
  const [description, setDescription] = useState("");
  const [minExp, setMinExp] = useState(2);
  const [maxExp, setMaxExp] = useState(5);
  const [education, setEducation] = useState("bachelor");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [preferredSkills, setPreferredSkills] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const skills = [
        ...splitSkills(requiredSkills).map((name) => ({ name, requirement_type: "required" as const })),
        ...splitSkills(preferredSkills).map((name) => ({ name, requirement_type: "preferred" as const })),
      ];
      const job = await apiRequest<Job>("/jobs", {
        method: "POST",
        body: {
          title,
          department: department || null,
          location: location || null,
          description,
          min_experience_years: minExp,
          max_experience_years: maxExp,
          required_education_level: education,
          skills,
        },
      });
      router.replace(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the job posting.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <div className="max-w-2xl">
        <h1 className="font-display text-2xl font-bold text-ink-900 mb-1">New job posting</h1>
        <p className="text-sm text-slate-500 mb-6">
          Jobs start as drafts. Publish once at least one required skill is defined.
        </p>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-card p-6 space-y-5">
          <Field label="Job title" required>
            <input required value={title} onChange={(e) => setTitle(e.target.value)} className={inputClass} />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Department">
              <input value={department} onChange={(e) => setDepartment(e.target.value)} className={inputClass} />
            </Field>
            <Field label="Location">
              <input value={location} onChange={(e) => setLocation(e.target.value)} className={inputClass} />
            </Field>
          </div>

          <Field label="Description" required>
            <textarea
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className={inputClass}
              placeholder="Describe the role, responsibilities, and what success looks like."
            />
          </Field>

          <div className="grid grid-cols-3 gap-4">
            <Field label="Min. experience (yrs)">
              <input
                type="number"
                min={0}
                value={minExp}
                onChange={(e) => setMinExp(Number(e.target.value))}
                className={inputClass}
              />
            </Field>
            <Field label="Max. experience (yrs)">
              <input
                type="number"
                min={0}
                value={maxExp}
                onChange={(e) => setMaxExp(Number(e.target.value))}
                className={inputClass}
              />
            </Field>
            <Field label="Required education">
              <select value={education} onChange={(e) => setEducation(e.target.value)} className={inputClass}>
                <option value="none">None</option>
                <option value="associate">Associate</option>
                <option value="bachelor">Bachelor</option>
                <option value="master">Master</option>
                <option value="doctorate">Doctorate</option>
              </select>
            </Field>
          </div>

          <Field label="Required skills" hint="Comma-separated, e.g. python, fastapi, postgresql">
            <input value={requiredSkills} onChange={(e) => setRequiredSkills(e.target.value)} className={inputClass} />
          </Field>
          <Field label="Preferred skills" hint="Comma-separated, e.g. docker, aws">
            <input value={preferredSkills} onChange={(e) => setPreferredSkills(e.target.value)} className={inputClass} />
          </Field>

          {error && <div className="rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700">{error}</div>}

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-ink-950 text-white text-sm font-semibold px-5 py-2.5 hover:bg-ink-900 transition-colors disabled:opacity-60"
            >
              {submitting ? "Creating…" : "Create job (draft)"}
            </button>
          </div>
        </form>
      </div>
    </Shell>
  );
}

const inputClass =
  "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-teal-accent focus:ring-1 focus:ring-teal-accent outline-none";

function Field({
  label,
  required,
  hint,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">
        {label} {required && <span className="text-rose-500">*</span>}
      </label>
      {children}
      {hint && <p className="text-xs text-slate-400 mt-1">{hint}</p>}
    </div>
  );
}

function splitSkills(raw: string): string[] {
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}
