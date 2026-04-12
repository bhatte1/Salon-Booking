from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenOut,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    generate_reset_token,
    get_reset_token_expiry,
)
from datetime import datetime, timezone
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup/customer", response_model=UserOut)
def customer_signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already registered")

    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role="customer",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login/customer", response_model=TokenOut)
def customer_login(payload: UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            or_(
                User.email == payload.username_or_email,
                User.username == payload.username_or_email,
            )
        )
        .first()
    )

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Not a customer account")

    token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/login/owner", response_model=TokenOut)
def owner_login(payload: UserLogin, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            or_(
                User.email == payload.username_or_email,
                User.username == payload.username_or_email,
            )
        )
        .first()
    )

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if user.role != "owner":
        raise HTTPException(status_code=403, detail="Not an owner account")

    token = create_access_token({"sub": str(user.id), "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }

@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # For security, don't reveal whether the email exists.
    if not user:
        return {
            "message": "If an account with that email exists, a reset link has been generated."
        }

    token = generate_reset_token()
    expires_at = get_reset_token_expiry()

    user.reset_token = token
    user.reset_token_expires_at = expires_at
    db.commit()

    reset_link = f"http://localhost:5173/reset-password?token={token}"

    return {
        "message": "If an account with that email exists, a reset link has been generated.",
        "reset_link": reset_link
    }


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == payload.token).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if not user.reset_token_expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    now_utc = datetime.now(timezone.utc)

    expiry = user.reset_token_expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < now_utc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(payload.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()

    return {"message": "Password has been reset successfully"}