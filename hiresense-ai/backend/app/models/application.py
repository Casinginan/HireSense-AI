from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.user import gen_uuid


class ApplicationStatus:
    APPLIED = "applied"
    SCREENED = "screened"
    ADVANCED = "advanced"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    HIRED = "hired"


class Application(Base):
    """Links a Candidate to a Job — the pipeline record."""

    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    status = Column(String, default=ApplicationStatus.APPLIED)
    applied_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    scores = relationship("Score", back_populates="application", cascade="all, delete-orphan")
    decisions = relationship("HRDecision", back_populates="application", cascade="all, delete-orphan")


class Score(Base):
    """A single scoring run's result for an application. Historical runs are retained, not overwritten."""

    __tablename__ = "scores"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)

    overall_score = Column(Float, nullable=False)
    suitability_label = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    # JSON-serialized (as text) breakdowns — kept as text for cross-DB (SQLite/Postgres) portability
    category_breakdown = Column(Text, nullable=False)  # {"skills": 88, "experience": 75, ...}
    matched_skills = Column(Text, nullable=False)  # JSON list
    missing_skills = Column(Text, nullable=False)  # JSON list
    explanation_factors = Column(Text, nullable=False)  # JSON list of {factor, impact, direction}
    recommendation_text = Column(Text, nullable=False)

    weights_snapshot = Column(Text, nullable=False)  # JSON of weights used for this run
    model_version = Column(String, default="rule-engine-v1.0")

    scored_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="scores")


class HRDecision(Base):
    __tablename__ = "hr_decisions"

    id = Column(String, primary_key=True, default=gen_uuid)
    application_id = Column(String, ForeignKey("applications.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)  # advance | reject | defer | hire
    note = Column(Text, nullable=True)
    ai_recommendation_snapshot = Column(Text, nullable=True)  # JSON: {"label": ..., "score": ...}
    decided_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="decisions")
