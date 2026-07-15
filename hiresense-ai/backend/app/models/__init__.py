from app.models.user import User, Role  # noqa: F401
from app.models.job import Job, JobSkill, Skill, JobStatus  # noqa: F401
from app.models.candidate import Candidate, CandidateSkill, Resume  # noqa: F401
from app.models.application import Application, Score, HRDecision, ApplicationStatus  # noqa: F401
from app.models.audit import AuditLog, Notification  # noqa: F401
from app.models.settings import SettingKV, ModelVersion  # noqa: F401
