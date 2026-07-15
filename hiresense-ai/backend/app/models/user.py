import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship

from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Role:
    ADMIN = "admin"
    HR_STAFF = "hr_staff"
    RECRUITER = "recruiter"
    HIRING_MANAGER = "hiring_manager"

    ALL = [ADMIN, HR_STAFF, RECRUITER, HIRING_MANAGER]


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default=Role.HR_STAFF)
    is_active = Column(Boolean, default=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    jobs_created = relationship("Job", back_populates="created_by_user")
