from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.user import gen_uuid


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    source = Column(String, default="direct_upload")

    total_experience_years = Column(Float, default=0)
    highest_education_level = Column(String, default="unknown")  # none/associate/bachelor/master/doctorate/unknown

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)

    candidate = relationship("Candidate", back_populates="skills")
    skill = relationship("Skill")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    raw_text = Column(Text, nullable=True)
    parser_confidence = Column(Float, default=0.0)
    parsed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="resumes")
