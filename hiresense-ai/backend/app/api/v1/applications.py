import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.deps import get_db, require_roles, log_audit
from app.models.user import User, Role
from app.models.job import Job, JobSkill
from app.models.candidate import Candidate, CandidateSkill, Resume
from app.models.application import Application, Score, HRDecision, ApplicationStatus
from app.models.settings import SettingKV, SCORING_WEIGHTS_KEY, DEFAULT_SCORING_WEIGHTS
from app.schemas.candidate import ApplicationOut, CandidateOut, ScoreOut, DecisionRequest, DecisionOut
from app.services.parser import parse_resume_file
from app.services.scoring import score_application

router = APIRouter(tags=["applications"])

EDITOR_ROLES = (Role.ADMIN, Role.HR_STAFF, Role.RECRUITER)
VIEWER_ROLES = (Role.ADMIN, Role.HR_STAFF, Role.RECRUITER, Role.HIRING_MANAGER)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _get_current_weights(db: Session) -> dict:
    row = db.query(SettingKV).filter(SettingKV.key == SCORING_WEIGHTS_KEY).first()
    if not row:
        return DEFAULT_SCORING_WEIGHTS
    return json.loads(row.value)


def _serialize_score(score: Score) -> ScoreOut:
    return ScoreOut(
        id=score.id,
        overall_score=score.overall_score,
        suitability_label=score.suitability_label,
        confidence=score.confidence,
        category_breakdown=json.loads(score.category_breakdown),
        matched_skills=json.loads(score.matched_skills),
        missing_skills=json.loads(score.missing_skills),
        explanation_factors=json.loads(score.explanation_factors),
        recommendation_text=score.recommendation_text,
        weights_snapshot=json.loads(score.weights_snapshot),
        model_version=score.model_version,
        scored_at=score.scored_at,
    )


def _serialize_candidate(candidate: Candidate) -> CandidateOut:
    return CandidateOut(
        id=candidate.id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        source=candidate.source,
        total_experience_years=candidate.total_experience_years,
        highest_education_level=candidate.highest_education_level,
        created_at=candidate.created_at,
        skills=[cs.skill.name for cs in candidate.skills],
    )


def _serialize_application(application: Application) -> ApplicationOut:
    latest = max(application.scores, key=lambda s: s.scored_at) if application.scores else None
    return ApplicationOut(
        id=application.id,
        job_id=application.job_id,
        candidate_id=application.candidate_id,
        status=application.status,
        applied_at=application.applied_at,
        candidate=_serialize_candidate(application.candidate),
        latest_score=_serialize_score(latest) if latest else None,
    )


def _run_scoring(db: Session, application: Application) -> Score:
    job: Job = application.job
    candidate: Candidate = application.candidate

    required_skills = [js.skill.name for js in job.job_skills if js.requirement_type == "required"]
    preferred_skills = [js.skill.name for js in job.job_skills if js.requirement_type == "preferred"]
    candidate_skill_names = [cs.skill.name for cs in candidate.skills]
    resume_text = candidate.resumes[-1].raw_text if candidate.resumes else ""

    weights = _get_current_weights(db)

    result = score_application(
        candidate_skills=candidate_skill_names,
        candidate_experience_years=candidate.total_experience_years,
        candidate_education_level=candidate.highest_education_level,
        resume_text=resume_text or "",
        job_required_skills=required_skills,
        job_preferred_skills=preferred_skills,
        job_min_experience=job.min_experience_years,
        job_max_experience=job.max_experience_years,
        job_required_education=job.required_education_level,
        job_description=job.description,
        weights=weights,
    )

    score = Score(
        application_id=application.id,
        overall_score=result.overall_score,
        suitability_label=result.suitability_label,
        confidence=result.confidence,
        category_breakdown=json.dumps(result.category_breakdown),
        matched_skills=json.dumps(result.matched_skills),
        missing_skills=json.dumps(result.missing_skills),
        explanation_factors=json.dumps(result.explanation_factors),
        recommendation_text=result.recommendation_text,
        weights_snapshot=json.dumps(result.weights_snapshot),
        model_version=result.model_version,
    )
    db.add(score)
    application.status = ApplicationStatus.SCREENED if application.status == ApplicationStatus.APPLIED else application.status
    db.commit()
    db.refresh(score)
    return score


@router.post("/jobs/{job_id}/resumes", response_model=list[ApplicationOut], status_code=201)
async def upload_resumes(
    job_id: str,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(require_roles(*EDITOR_ROLES)),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    os.makedirs(app_settings.UPLOAD_DIR, exist_ok=True)
    results: list[ApplicationOut] = []
    errors: list[dict] = []

    for upload in files:
        ext = os.path.splitext(upload.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append({"file": upload.filename, "error": "Unsupported file type. Only PDF and DOCX are accepted."})
            continue

        content = await upload.read()
        if len(content) > app_settings.MAX_UPLOAD_MB * 1024 * 1024:
            errors.append({"file": upload.filename, "error": f"File exceeds the {app_settings.MAX_UPLOAD_MB}MB limit."})
            continue

        try:
            parsed = parse_resume_file(content, upload.filename or "resume")
        except Exception as exc:  # noqa: BLE001
            errors.append({"file": upload.filename, "error": f"Could not parse file: {exc}"})
            continue

        stored_name = f"{uuid.uuid4()}{ext}"
        stored_path = os.path.join(app_settings.UPLOAD_DIR, stored_name)
        with open(stored_path, "wb") as f:
            f.write(content)

        candidate = None
        if parsed.email:
            candidate = db.query(Candidate).filter(Candidate.email == parsed.email).first()
        if not candidate:
            candidate = Candidate(
                full_name=parsed.full_name_guess or (upload.filename or "Unknown Candidate").rsplit(".", 1)[0],
                email=parsed.email,
                phone=parsed.phone,
                total_experience_years=parsed.total_experience_years,
                highest_education_level=parsed.highest_education_level,
            )
            db.add(candidate)
            db.flush()
        else:
            # Update with the latest resume's derived data (most recent resume wins, per SRS 7.7)
            candidate.total_experience_years = parsed.total_experience_years
            candidate.highest_education_level = parsed.highest_education_level

        db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate.id).delete()
        from app.api.v1.jobs import _get_or_create_skill  # local import to avoid circularity at module load
        for skill_name in parsed.skills:
            skill = _get_or_create_skill(db, skill_name)
            db.add(CandidateSkill(candidate_id=candidate.id, skill_id=skill.id))

        resume = Resume(
            candidate_id=candidate.id,
            file_name=upload.filename or stored_name,
            file_path=stored_path,
            raw_text=parsed.raw_text,
            parser_confidence=parsed.confidence,
        )
        db.add(resume)
        db.flush()

        application = db.query(Application).filter(
            Application.candidate_id == candidate.id, Application.job_id == job.id
        ).first()
        if not application:
            application = Application(candidate_id=candidate.id, job_id=job.id)
            db.add(application)
            db.flush()

        db.commit()
        db.refresh(application)

        _run_scoring(db, application)
        db.refresh(application)

        results.append(_serialize_application(application))

    log_audit(
        db, user_id=current_user.id, event_type="resumes_uploaded", entity_type="job", entity_id=job.id,
        details={"succeeded": len(results), "failed": len(errors), "errors": errors},
    )

    if not results and errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    return results


@router.get("/jobs/{job_id}/applications", response_model=list[ApplicationOut])
def list_applications(
    job_id: str,
    sort: str = Query("score_desc", description="score_desc | score_asc | recent"),
    current_user: User = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    applications = db.query(Application).filter(Application.job_id == job_id).all()
    serialized = [_serialize_application(a) for a in applications]

    def sort_key(a: ApplicationOut):
        score = a.latest_score.overall_score if a.latest_score else -1
        return score

    if sort == "score_asc":
        serialized.sort(key=sort_key)
    elif sort == "recent":
        serialized.sort(key=lambda a: a.applied_at, reverse=True)
    else:
        serialized.sort(key=sort_key, reverse=True)

    return serialized


@router.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: str, current_user: User = Depends(require_roles(*VIEWER_ROLES)), db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return _serialize_candidate(candidate)


@router.get("/applications/compare", response_model=list[ApplicationOut])
def compare_applications(
    application_ids: str = Query(..., description="Comma-separated application IDs"),
    current_user: User = Depends(require_roles(*VIEWER_ROLES)),
    db: Session = Depends(get_db),
):
    ids = [i.strip() for i in application_ids.split(",") if i.strip()]
    if len(ids) < 2:
        raise HTTPException(status_code=422, detail="Provide at least two application_ids to compare.")
    applications = db.query(Application).filter(Application.id.in_(ids)).all()
    if len(applications) != len(ids):
        raise HTTPException(status_code=404, detail="One or more applications were not found.")
    return [_serialize_application(a) for a in applications]


@router.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(application_id: str, current_user: User = Depends(require_roles(*VIEWER_ROLES)), db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    return _serialize_application(application)


@router.get("/applications/{application_id}/score", response_model=ScoreOut)
def get_application_score(application_id: str, current_user: User = Depends(require_roles(*VIEWER_ROLES)), db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    if not application.scores:
        raise HTTPException(status_code=404, detail="This application has not been scored yet.")
    latest = max(application.scores, key=lambda s: s.scored_at)
    return _serialize_score(latest)


@router.post("/applications/{application_id}/rescore", response_model=ScoreOut)
def rescore_application(application_id: str, current_user: User = Depends(require_roles(*EDITOR_ROLES)), db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    score = _run_scoring(db, application)
    log_audit(db, user_id=current_user.id, event_type="application_rescored", entity_type="application", entity_id=application.id)
    return _serialize_score(score)


@router.post("/applications/{application_id}/decision", response_model=DecisionOut)
def record_decision(
    application_id: str,
    payload: DecisionRequest,
    current_user: User = Depends(require_roles(Role.ADMIN, Role.HR_STAFF, Role.HIRING_MANAGER)),
    db: Session = Depends(get_db),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")

    if payload.action not in ("advance", "reject", "defer", "hire"):
        raise HTTPException(status_code=422, detail="action must be one of: advance, reject, defer, hire")

    latest_score = max(application.scores, key=lambda s: s.scored_at) if application.scores else None
    snapshot = {"label": latest_score.suitability_label, "score": latest_score.overall_score} if latest_score else None

    decision = HRDecision(
        application_id=application.id,
        user_id=current_user.id,
        action=payload.action,
        note=payload.note,
        ai_recommendation_snapshot=json.dumps(snapshot) if snapshot else None,
    )
    db.add(decision)

    status_map = {
        "advance": ApplicationStatus.ADVANCED,
        "reject": ApplicationStatus.REJECTED,
        "defer": ApplicationStatus.NEEDS_REVIEW,
        "hire": ApplicationStatus.HIRED,
    }
    application.status = status_map[payload.action]

    db.commit()
    db.refresh(decision)

    log_audit(
        db, user_id=current_user.id, event_type="decision_recorded", entity_type="application", entity_id=application.id,
        details={"action": payload.action, "ai_recommendation_snapshot": snapshot},
    )

    return DecisionOut(
        id=decision.id,
        application_id=decision.application_id,
        user_id=decision.user_id,
        action=decision.action,
        note=decision.note,
        ai_recommendation_snapshot=snapshot,
        decided_at=decision.decided_at,
    )



