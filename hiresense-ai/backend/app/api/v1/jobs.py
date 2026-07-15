from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles, log_audit, get_current_user
from app.models.user import User, Role
from app.models.job import Job, JobSkill, Skill, JobStatus
from app.models.application import Application
from app.schemas.job import JobCreate, JobUpdate, JobOut, JobSkillOut

router = APIRouter(prefix="/jobs", tags=["jobs"])

EDITOR_ROLES = (Role.ADMIN, Role.HR_STAFF, Role.RECRUITER)
VIEWER_ROLES = (Role.ADMIN, Role.HR_STAFF, Role.RECRUITER, Role.HIRING_MANAGER)


def _get_or_create_skill(db: Session, name: str) -> Skill:
    normalized = name.strip()
    skill = db.query(Skill).filter(Skill.name.ilike(normalized)).first()
    if not skill:
        skill = Skill(name=normalized)
        db.add(skill)
        db.flush()
    return skill


def _serialize_job(db: Session, job: Job) -> JobOut:
    applicant_count = db.query(Application).filter(Application.job_id == job.id).count()
    out = JobOut.model_validate(job)
    out.applicant_count = applicant_count
    out.skills = [JobSkillOut(name=js.skill.name, requirement_type=js.requirement_type) for js in job.job_skills]
    return out


@router.get("", response_model=list[JobOut])
def list_jobs(
    status_filter: str | None = Query(None, alias="status"),
    current_user: User = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    jobs = query.order_by(Job.created_at.desc()).all()
    return [_serialize_job(db, j) for j in jobs]


@router.post("", response_model=JobOut, status_code=201)
def create_job(payload: JobCreate, current_user: User = Depends(require_roles(*EDITOR_ROLES)), db: Session = Depends(get_db)):
    job = Job(
        title=payload.title,
        department=payload.department,
        location=payload.location,
        employment_type=payload.employment_type,
        description=payload.description,
        min_experience_years=payload.min_experience_years,
        max_experience_years=payload.max_experience_years,
        required_education_level=payload.required_education_level,
        status=JobStatus.DRAFT,
        created_by=current_user.id,
    )
    db.add(job)
    db.flush()

    for s in payload.skills:
        skill = _get_or_create_skill(db, s.name)
        db.add(JobSkill(job_id=job.id, skill_id=skill.id, requirement_type=s.requirement_type))

    db.commit()
    db.refresh(job)
    log_audit(db, user_id=current_user.id, event_type="job_created", entity_type="job", entity_id=job.id)
    return _serialize_job(db, job)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, current_user: User = Depends(require_roles(*VIEWER_ROLES)), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return _serialize_job(db, job)


@router.put("/{job_id}", response_model=JobOut)
def update_job(job_id: str, payload: JobUpdate, current_user: User = Depends(require_roles(*EDITOR_ROLES)), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    data = payload.model_dump(exclude_unset=True, exclude={"skills"})
    for field, value in data.items():
        setattr(job, field, value)

    if payload.skills is not None:
        db.query(JobSkill).filter(JobSkill.job_id == job.id).delete()
        for s in payload.skills:
            skill = _get_or_create_skill(db, s.name)
            db.add(JobSkill(job_id=job.id, skill_id=skill.id, requirement_type=s.requirement_type))

    db.commit()
    db.refresh(job)
    log_audit(db, user_id=current_user.id, event_type="job_updated", entity_type="job", entity_id=job.id)
    return _serialize_job(db, job)


@router.post("/{job_id}/publish", response_model=JobOut)
def publish_job(job_id: str, current_user: User = Depends(require_roles(*EDITOR_ROLES)), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    required_skills = [js for js in job.job_skills if js.requirement_type == "required"]
    errors = []
    if not job.title:
        errors.append("Title is required.")
    if not job.description:
        errors.append("Description is required.")
    if not required_skills:
        errors.append("At least one required skill must be defined before publishing.")
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    job.status = JobStatus.PUBLISHED
    db.commit()
    db.refresh(job)
    log_audit(db, user_id=current_user.id, event_type="job_published", entity_type="job", entity_id=job.id)
    return _serialize_job(db, job)


@router.post("/{job_id}/close", response_model=JobOut)
def close_job(job_id: str, current_user: User = Depends(require_roles(*EDITOR_ROLES)), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    job.status = JobStatus.CLOSED
    db.commit()
    db.refresh(job)
    log_audit(db, user_id=current_user.id, event_type="job_closed", entity_type="job", entity_id=job.id)
    return _serialize_job(db, job)
