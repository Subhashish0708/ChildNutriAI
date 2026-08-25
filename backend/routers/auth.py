"""
Authentication Endpoints: Register, Login, Me, Logout
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import UserRegister, UserLogin, UserResponse, TokenResponse
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (parent, health_worker, etc.). Passwords hashed with bcrypt."""
    email_clean = payload.email.lower().strip()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )
    
    # Assemble full_name from any available fields
    parts = []
    if payload.first_name: parts.append(payload.first_name.strip())
    if payload.last_name: parts.append(payload.last_name.strip())
    combined_fl = " ".join(parts).strip()

    name = (
        payload.full_name or 
        payload.name or 
        combined_fl or 
        email_clean.split("@")[0].capitalize()
    ).strip()

    if not name:
        name = "User"

    # Map role cleanly
    role = (payload.role or "parent").lower().strip()
    if any(k in role for k in ["health", "worker", "doctor", "anganwadi", "nurse", "pediatrician", "nutritionist", "researcher"]):
        role = "health_worker"
    elif "admin" in role:
        role = "admin"
    else:
        role = "parent"

    new_user = User(
        full_name=name,
        email=email_clean,
        phone=payload.phone.strip() if payload.phone else None,
        password_hash=hash_password(payload.password),
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user with email/password and issue signed JWT."""
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return profile details for the currently logged-in user."""
    return current_user


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Informational logout endpoint. Frontend drops stored JWT."""
    return {"message": "Successfully logged out.", "status": "ok"}
