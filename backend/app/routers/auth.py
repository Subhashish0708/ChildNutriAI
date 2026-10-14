"""Auth router — signup, login, logout, refresh, me"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, RefreshToken
from backend.app.schemas import SignupRequest, LoginRequest, UserOut
from backend.app.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from backend.app.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_OPTS = dict(httponly=True, samesite="lax", secure=False)  # secure=True in production (HTTPS)


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(body: SignupRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email,
        full_name=body.full_name,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _set_tokens(response, db, user)
    return user


@router.post("/login", response_model=UserOut)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")
    _set_tokens(response, db, user)
    return user


@router.post("/logout")
def logout(response: Response,
           refresh_token: str = Cookie(default=None),
           db: Session = Depends(get_db)):
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                rt = db.query(RefreshToken).filter_by(jti=jti).first()
                if rt:
                    rt.revoked = True
                    db.commit()
        except Exception:
            pass
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.post("/refresh", response_model=UserOut)
def refresh(response: Response,
            refresh_token: str = Cookie(default=None),
            db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        jti = payload.get("jti")
        rt = db.query(RefreshToken).filter_by(jti=jti).first()
        if not rt or rt.revoked:
            raise ValueError("Revoked token")
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    _set_tokens(response, db, user)
    return user


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.delete("/me", status_code=204)
def delete_me(
    response: Response,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete the current account and all owned child data."""
    db.delete(user)
    db.commit()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _set_tokens(response: Response, db: Session, user: User):
    access = create_access_token(user.id, user.role)
    refresh, jti, exp = create_refresh_token(user.id)

    # Store refresh token in DB
    rt = RefreshToken(jti=jti, user_id=user.id, expires_at=exp)
    db.add(rt)
    db.commit()

    response.set_cookie("access_token", access, **COOKIE_OPTS, max_age=30 * 60)
    response.set_cookie("refresh_token", refresh, **COOKIE_OPTS, max_age=7 * 24 * 3600)
