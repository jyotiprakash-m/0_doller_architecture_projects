"""
Authentication Router for Synthetic Data Generator.
Handles user registration, login, and profile retrieval.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from services import db
from services.auth_utils import get_password_hash, verify_password, create_access_token, get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    credits: int

@router.post("/register", response_model=dict)
async def register(user_data: UserRegister):
    """Register a new user account."""
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(user_data.password)
    new_user = db.create_user(user_data.email, hashed_pw)
    
    if not new_user:
        raise HTTPException(status_code=500, detail="Failed to create account")
        
    logger.info(f"New user registered: {user_data.email}")
    return {"message": "User registered successfully", "user_id": new_user["id"]}

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a user and return a JWT access token."""
    user = db.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["id"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user_id": user["id"],
        "credits": user["credits"]
    }

@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    """Get current user profile."""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "email": user["email"],
        "credits": user["credits"],
        "created_at": user["created_at"]
    }
