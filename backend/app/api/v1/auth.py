from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_current_user 
from app.infrastructure.db.session import get_db
from app.domain.models import User, Settings
from app.domain.schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
)
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token 

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=user_in.email, password_hash=hash_password(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=str(user.id),
        email=user.email,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(str(user.id), db)
    return TokenResponse(access_token=token, refresh_token=refresh_token)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"status": "ok", "message": "Password updated successfully."}


@router.get("/settings", response_model=UserSettingsResponse)
def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings_obj = db.query(Settings).filter(Settings.user_id == current_user.id).first()
    if not settings_obj:
        settings_obj = Settings(user_id=current_user.id, theme="dark", default_exchange="NSE")
        db.add(settings_obj)
        db.commit()
        db.refresh(settings_obj)
    return UserSettingsResponse(
        theme=settings_obj.theme or "dark",
        default_exchange=settings_obj.default_exchange,
        email_alerts=False,
    )


@router.patch("/settings", response_model=UserSettingsResponse)
def update_user_settings(
    payload: UserSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings_obj = db.query(Settings).filter(Settings.user_id == current_user.id).first()
    if not settings_obj:
        settings_obj = Settings(user_id=current_user.id)
        db.add(settings_obj)

    if payload.theme is not None:
        settings_obj.theme = payload.theme
    if payload.default_exchange is not None:
        settings_obj.default_exchange = payload.default_exchange

    db.commit()
    db.refresh(settings_obj)
    return UserSettingsResponse(
        theme=settings_obj.theme or "dark",
        default_exchange=settings_obj.default_exchange,
        email_alerts=payload.email_alerts if payload.email_alerts is not None else False,
    )
    