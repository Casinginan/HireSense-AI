from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, log_audit, get_current_user
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, AccessTokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    generic_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not user:
        # Do not reveal whether the email exists (SRS 7.1 validation rule)
        raise generic_error

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account temporarily locked due to repeated failed login attempts.")

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        db.commit()
        log_audit(db, user_id=user.id, event_type="login_failed", entity_type="user", entity_id=user.id)
        raise generic_error

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    log_audit(db, user_id=user.id, event_type="login_success", entity_type="user", entity_id=user.id)

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    user = db.query(User).filter(User.id == token_data["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    return AccessTokenResponse(access_token=create_access_token(user.id, user.role))


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Refresh tokens are stateless JWTs in this scaffold; a production system would maintain
    # a revocation list/table keyed by token id (jti) to truly invalidate refresh tokens.
    log_audit(db, user_id=current_user.id, event_type="logout", entity_type="user", entity_id=current_user.id)
    return {"detail": "Logged out."}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
    }
