"""
Auth Router — User registration, login, JWT token management.
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr

from services import db
from services.auth_utils import (
    hash_password, verify_password, create_access_token, get_current_user_id
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(req: RegisterRequest):
    """Register a new user."""
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    hashed = hash_password(req.password)
    user = db.create_user(email=req.email, hashed_password=hashed, full_name=req.full_name)

    if not user:
        raise HTTPException(status_code=409, detail="Email already registered")

    token = create_access_token(user["id"])
    logger.info(f"New user registered: {req.email}")

    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"],
                 "full_name": user["full_name"], "credits": user["credits"]},
    }


@router.post("/login")
async def login(req: LoginRequest):
    """Login and get JWT token."""
    user = db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["id"])
    logger.info(f"User logged in: {req.email}")

    return {
        "token": token,
        "user": {"id": user["id"], "email": user["email"],
                 "full_name": user.get("full_name", ""), "credits": user["credits"]},
    }


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    """Get current user profile and stats."""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "role": user.get("role", "trainee"),
        "credits": user["credits"],
    }
