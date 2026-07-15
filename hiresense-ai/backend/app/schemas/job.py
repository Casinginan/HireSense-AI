from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class JobSkillIn(BaseModel):
    name: str
    requirement_type: str = "required"  # required | preferred


class JobCreate(BaseModel):
    title: str
    department: str | None = None
    location: str | None = None
    employment_type: str = "full_time"
    description: str = ""
    min_experience_years: float = 0
    max_experience_years: float = 5
    required_education_level: str = "bachelor"
    skills: list[JobSkillIn] = []

    @field_validator("skills")
    @classmethod
    def must_have_at_least_one_required_skill_eventually(cls, v):
        return v


class JobUpdate(BaseModel):
    title: str | None = None
    department: str | None = None
    location: str | None = None
    employment_type: str | None = None
    description: str | None = None
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    required_education_level: str | None = None
    skills: list[JobSkillIn] | None = None


class JobSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    requirement_type: str


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    department: str | None
    location: str | None
    employment_type: str
    description: str
    status: str
    min_experience_years: float
    max_experience_years: float
    required_education_level: str
    created_at: datetime
    updated_at: datetime
    skills: list[JobSkillOut] = []
    applicant_count: int = 0
