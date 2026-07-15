import json
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.models.audit import AuditLog

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def log_audit(db: Session, *, user_id: str | None, event_type: str, entity_type: str | None = None,
              entity_id: str | None = None, details: dict | None = None) -> None:
    entry = AuditLog(
        user_id=user_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details=json.dumps(details or {}),
    )
    db.add(entry)
    db.commit()


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: str):
    def dependency(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        if current_user.role not in allowed_roles:
            log_audit(
                db,
                user_id=current_user.id,
                event_type="permission_denied",
                entity_type="endpoint",
                details={"required_roles": list(allowed_roles), "user_role": current_user.role},
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action.")
        return current_user
    return dependency
