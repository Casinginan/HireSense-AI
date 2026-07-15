from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer

from app.db.session import Base
from app.models.user import gen_uuid

SCORING_WEIGHTS_KEY = "scoring_weights"
RETENTION_POLICY_KEY = "retention_policy_days"

DEFAULT_SCORING_WEIGHTS = {
    "skills": 35,
    "experience": 25,
    "education": 15,
    "certifications": 10,
    "projects": 10,
    "semantic_similarity": 5,
}


class SettingKV(Base):
    __tablename__ = "settings"

    id = Column(String, primary_key=True, default=gen_uuid)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=False)  # JSON string
    version = Column(Integer, default=1)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ModelVersion(Base):
    """Tracks the AI scoring engine version in use. In this MVP scaffold the 'model' is a
    transparent, rule-based weighted scoring engine (see app/services/scoring.py) rather than
    a trained ML classifier — see README for how to plug in a trained model later."""

    __tablename__ = "model_versions"

    id = Column(String, primary_key=True, default=gen_uuid)
    version_label = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False)
    trained_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
