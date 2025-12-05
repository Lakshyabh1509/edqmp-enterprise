"""
EDQMP Authentication API
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client

from app.core.config import settings
from app.core.database import get_supabase
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user
)
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    supabase: Client = Depends(get_supabase)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # 1. Try to find user in our 'users' table (if we had one separate from Supabase Auth)
    # For this implementation, we'll use Supabase Auth directly via the client
    
    try:
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        user = auth_response.user
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Create our own JWT token for internal use (or pass through Supabase session)
        # We'll create our own to control the claims and expiration
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": "admin"}, # Default to admin for MVP
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": "admin"
            }
        }
        
    except Exception as e:
        # Fallback for demo/testing if Supabase isn't configured yet
        if settings.environment == "development" and form_data.username == "admin@edqmp.com":
             access_token = create_access_token(
                data={"sub": "00000000-0000-0000-0000-000000000000", "email": "admin@edqmp.com", "role": "admin"}
            )
             return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {"id": "dev-id", "email": "admin@edqmp.com", "role": "admin"}
            }
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/signup", response_model=Token)
async def signup(
    user_data: UserCreate,
    supabase: Client = Depends(get_supabase)
):
    """Register a new user"""
    try:
        # Register with Supabase
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name
                }
            }
        })
        
        user = auth_response.user
        if not user:
             raise HTTPException(status_code=400, detail="Registration failed")

        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": "user"}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user_data.full_name
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current user details"""
    return current_user
