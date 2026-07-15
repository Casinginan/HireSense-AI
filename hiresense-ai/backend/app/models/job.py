from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.user import gen_uuid


class JobStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=True)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    department = Column(String, nullable=True)
    location = Column(String, nullable=True)
    employment_type = Column(String, default="full_time")
    description = Column(Text, nullable=False, default="")
    status = Column(String, default=JobStatus.DRAFT)

    min_experience_years = Column(Float, default=0)
    max_experience_years = Column(Float, default=5)
    required_education_level = Column(String, default="bachelor")  # none/associate/bachelor/master/doctorate

    # Optional per-job override of global scoring weights (JSON stored as text via SQLAlchemy JSON below)
    custom_weights = Column(String, nullable=True)  # JSON string, nullable => use global default

    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    created_by_user = relationship("User", back_populates="jobs_created")
    job_skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(String, primary_key=True, default=gen_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    requirement_type = Column(String, default="required")  # required | preferred

    job = relationship("Job", back_populates="job_skills")
    skill = relationship("Skill")
