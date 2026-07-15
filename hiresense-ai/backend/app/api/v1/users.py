from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_roles, log_audit, get_current_user
from app.core.security import hash_password
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(current_user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, current_user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    if payload.role not in Role.ALL:
        raise HTTPException(status_code=422, detail=f"Role must be one of {Role.ALL}")
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email already exists.")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_audit(db, user_id=current_user.id, event_type="user_created", entity_type="user", entity_id=user.id)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, current_user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if user.role == Role.ADMIN and payload.is_active is False:
        remaining_admins = db.query(User).filter(User.role == Role.ADMIN, User.is_active == True, User.id != user_id).count()  # noqa: E712
        if remaining_admins == 0:
            raise HTTPException(status_code=400, detail="Cannot deactivate the sole remaining Administrator account.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    log_audit(db, user_id=current_user.id, event_type="user_updated", entity_type="user", entity_id=user.id, details=payload.model_dump(exclude_unset=True))
    return user
