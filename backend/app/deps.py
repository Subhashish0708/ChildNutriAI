"""
ChildNutri AI — FastAPI dependencies
"""
from typing import Optional
from fastapi import Depends, HTTPException, Cookie, Header, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, RefreshToken
from backend.app.security import decode_token


def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = access_token
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_health_worker(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("health_worker", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Health worker access required")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
