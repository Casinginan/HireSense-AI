from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    email: str | None
    phone: str | None
    source: str
    total_experience_years: float
    highest_education_level: str
    created_at: datetime
    skills: list[str] = []


class ScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    overall_score: float
    suitability_label: str
    confidence: float
    category_breakdown: dict
    matched_skills: list[str]
    missing_skills: list[str]
    explanation_factors: list[dict]
    recommendation_text: str
    weights_snapshot: dict
    model_version: str
    scored_at: datetime


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    candidate_id: str
    status: str
    applied_at: datetime
    candidate: CandidateOut | None = None
    latest_score: ScoreOut | None = None


class DecisionRequest(BaseModel):
    action: str  # advance | reject | defer | hire
    note: str | None = None


class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    application_id: str
    user_id: str
    action: str
    note: str | None
    ai_recommendation_snapshot: dict | None
    decided_at: datetime
