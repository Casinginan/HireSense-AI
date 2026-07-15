export interface JobSkill {
  name: string;
  requirement_type: "required" | "preferred";
}

export interface Job {
  id: string;
  title: string;
  department: string | null;
  location: string | null;
  employment_type: string;
  description: string;
  status: "draft" | "published" | "closed" | "archived";
  min_experience_years: number;
  max_experience_years: number;
  required_education_level: string;
  created_at: string;
  updated_at: string;
  skills: JobSkill[];
  applicant_count: number;
}

export interface Candidate {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  source: string;
  total_experience_years: number;
  highest_education_level: string;
  created_at: string;
  skills: string[];
}

export interface ExplanationFactor {
  factor: string;
  value: number | null;
  direction: "positive" | "neutral" | "negative";
}

export interface Score {
  id: string;
  overall_score: number;
  suitability_label: string;
  confidence: number;
  category_breakdown: Record<string, number>;
  matched_skills: string[];
  missing_skills: string[];
  explanation_factors: ExplanationFactor[];
  recommendation_text: string;
  weights_snapshot: Record<string, number>;
  model_version: string;
  scored_at: string;
}

export interface Application {
  id: string;
  job_id: string;
  candidate_id: string;
  status: string;
  applied_at: string;
  candidate: Candidate | null;
  latest_score: Score | null;
}

export interface ScoringWeights {
  skills: number;
  experience: number;
  education: number;
  certifications: number;
  projects: number;
  semantic_similarity: number;
}

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AnalyticsSummary {
  total_jobs: number;
  published_jobs: number;
  total_applications: number;
  hiring_funnel: Record<string, number>;
  average_match_score: number | null;
  scored_applications: number;
}
