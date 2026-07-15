from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text

from app.db.session import Base
from app.models.user import gen_uuid


class AuditLog(Base):
    """Append-only audit trail. No API path should ever update or delete a row here."""

    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, nullable=True)  # nullable for system-generated events
    event_type = Column(String, nullable=False)  # e.g. "login_failed", "decision_recorded", "settings_updated"
    entity_type = Column(String, nullable=True)  # e.g. "application", "job", "user"
    entity_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(Text, nullable=True)  # JSON string
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
