"""
Run with:  python -m app.seed
Creates the database tables (if not already present) and seeds:
  - one Administrator account
  - one HR Staff account
  - one Hiring Manager account
  - a sample published job
  - the default scoring-weight configuration
  - an active model-version record describing the rule-based scoring engine
"""
import json

from app.db.session import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.job import Job, JobSkill, Skill, JobStatus
from app.models.settings import SettingKV, ModelVersion, SCORING_WEIGHTS_KEY, DEFAULT_SCORING_WEIGHTS
import app.models  # noqa: F401


def _get_or_create_skill(db, name: str) -> Skill:
    skill = db.query(Skill).filter(Skill.name.ilike(name)).first()
    if not skill:
        skill = Skill(name=name)
        db.add(skill)
        db.flush()
    return skill


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == "admin@hiresense.ai").first():
            db.add(User(
                full_name="System Administrator",
                email="admin@hiresense.ai",
                password_hash=hash_password("Admin123!"),
                role=Role.ADMIN,
            ))
        if not db.query(User).filter(User.email == "hr@hiresense.ai").first():
            db.add(User(
                full_name="Jordan Reyes",
                email="hr@hiresense.ai",
                password_hash=hash_password("HrStaff123!"),
                role=Role.HR_STAFF,
            ))
        if not db.query(User).filter(User.email == "manager@hiresense.ai").first():
            db.add(User(
                full_name="Casey Lin",
                email="manager@hiresense.ai",
                password_hash=hash_password("Manager123!"),
                role=Role.HIRING_MANAGER,
            ))
        db.commit()

        if not db.query(SettingKV).filter(SettingKV.key == SCORING_WEIGHTS_KEY).first():
            db.add(SettingKV(key=SCORING_WEIGHTS_KEY, value=json.dumps(DEFAULT_SCORING_WEIGHTS), version=1))
            db.commit()

        if not db.query(ModelVersion).filter(ModelVersion.version_label == "rule-engine-v1.0").first():
            db.add(ModelVersion(
                version_label="rule-engine-v1.0",
                description="Transparent, rule-based weighted scoring engine (MVP scaffold). See README for how to plug in a trained XGBoost + SHAP pipeline.",
                is_active=True,
            ))
            db.commit()

        if not db.query(Job).filter(Job.title == "Backend Engineer II").first():
            job = Job(
                title="Backend Engineer II",
                department="Engineering",
                location="Remote",
                employment_type="full_time",
                description=(
                    "We are looking for a Backend Engineer II to design and build REST APIs, "
                    "work with PostgreSQL and Redis, and collaborate closely with our frontend "
                    "and AI/ML teams on a modern, cloud-native platform."
                ),
                status=JobStatus.PUBLISHED,
                min_experience_years=3,
                max_experience_years=6,
                required_education_level="bachelor",
            )
            db.add(job)
            db.flush()

            required = ["python", "fastapi", "postgresql", "rest api"]
            preferred = ["docker", "redis", "aws"]
            for name in required:
                skill = _get_or_create_skill(db, name)
                db.add(JobSkill(job_id=job.id, skill_id=skill.id, requirement_type="required"))
            for name in preferred:
                skill = _get_or_create_skill(db, name)
                db.add(JobSkill(job_id=job.id, skill_id=skill.id, requirement_type="preferred"))
            db.commit()

        print("Seed complete.")
        print("Login with: admin@hiresense.ai / Admin123!  (Administrator)")
        print("            hr@hiresense.ai / HrStaff123!    (HR Staff)")
        print("            manager@hiresense.ai / Manager123! (Hiring Manager)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
