from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ScoringWeightsIn(BaseModel):
    skills: float
    experience: float
    education: float
    certifications: float
    projects: float
    semantic_similarity: float

    @field_validator("semantic_similarity")
    @classmethod
    def weights_must_sum_to_100(cls, v, info):
        total = (
            info.data.get("skills", 0)
            + info.data.get("experience", 0)
            + info.data.get("education", 0)
            + info.data.get("certifications", 0)
            + info.data.get("projects", 0)
            + v
        )
        if abs(total - 100) > 0.01:
            raise ValueError(f"Scoring weights must sum to 100 (current sum: {total}).")
        return v


class ScoringWeightsOut(ScoringWeightsIn):
    pass


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str | None
    event_type: str
    entity_type: str | None
    entity_id: str | None
    details: dict | None
    created_at: datetime
