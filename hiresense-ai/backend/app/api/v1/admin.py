import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles, log_audit
from app.models.user import User, Role
from app.models.settings import SettingKV, ModelVersion, SCORING_WEIGHTS_KEY, DEFAULT_SCORING_WEIGHTS
from app.models.audit import AuditLog
from app.models.job import Job, JobStatus
from app.models.application import Application, Score, ApplicationStatus
from app.schemas.admin import ScoringWeightsIn, ScoringWeightsOut, AuditLogOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/settings/scoring-weights", response_model=ScoringWeightsOut)
def get_scoring_weights(current_user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    row = db.query(SettingKV).filter(SettingKV.key == SCORING_WEIGHTS_KEY).first()
    weights = json.loads(row.value) if row else DEFAULT_SCORING_WEIGHTS
    return ScoringWeightsOut(**weights)


@router.put("/settings/scoring-weights", response_model=ScoringWeightsOut)
def update_scoring_weights(payload: ScoringWeightsIn, current_user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    row = db.query(SettingKV).filter(SettingKV.key == SCORING_WEIGHTS_KEY).first()
    weights_dict = payload.model_dump()
    if row:
        row.value = json.dumps(weights_dict)
        row.version = (row.version or 1) + 1
        row.updated_by = current_user.id
    else:
        row = SettingKV(key=SCORING_WEIGHTS_KEY, value=json.dumps(weights_dict), version=1, updated_by=current_user.id)
        db.add(row)
    db.commit()

    log_audit(db, user_id=current_user.id, event_type="settings_updated", entity_type="settings", entity_id=SCORING_WEIGHTS_KEY, details=weights_dict)
    return ScoringWeightsOut(**weights_dict)


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = Query(100, le=1000),
    current_user: User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    out = []
    for log in logs:
        out.append(AuditLogOut(
            id=log.id,
            user_id=log.user_id,
            event_type=log.event_type,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=json.loads(log.details) if log.details else None,
            created_at=log.created_at,
        ))
    return out


@router.get("/model-versions")
def list_model_versions(current_user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    versions = db.query(ModelVersion).order_by(ModelVersion.trained_at.desc()).all()
    return [
        {
            "id": v.id,
            "version_label": v.version_label,
            "description": v.description,
            "is_active": v.is_active,
            "trained_at": v.trained_at,
        }
        for v in versions
    ]


@router.get("/analytics/summary")
def analytics_summary(current_user: User = Depends(require_roles(Role.ADMIN, Role.HR_STAFF, Role.RECRUITER, Role.HIRING_MANAGER)), db: Session = Depends(get_db)):
    total_jobs = db.query(Job).count()
    published_jobs = db.query(Job).filter(Job.status == JobStatus.PUBLISHED).count()
    total_applications = db.query(Application).count()

    funnel = {}
    for status_value in (
        ApplicationStatus.APPLIED, ApplicationStatus.SCREENED, ApplicationStatus.ADVANCED,
        ApplicationStatus.NEEDS_REVIEW, ApplicationStatus.REJECTED, ApplicationStatus.HIRED,
    ):
        funnel[status_value] = db.query(Application).filter(Application.status == status_value).count()

    scores = db.query(Score.overall_score).all()
    score_values = [s[0] for s in scores]
    avg_score = round(sum(score_values) / len(score_values), 1) if score_values else None

    return {
        "total_jobs": total_jobs,
        "published_jobs": published_jobs,
        "total_applications": total_applications,
        "hiring_funnel": funnel,
        "average_match_score": avg_score,
        "scored_applications": len(score_values),
    }
