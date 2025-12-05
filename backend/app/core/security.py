"""
EDQMP Security Utilities
JWT authentication and authorization helpers
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from supabase import Client

from app.core.config import settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer(auto_error=False)


class TokenData:
    """Decoded token data"""
    def __init__(self, user_id: str, email: str, role: str = "user"):
        self.user_id = user_id
        self.email = email
        self.role = role


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        email = payload.get("email", "")
        role = payload.get("role", "user")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, email=email, role=role)
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        return None


async def verify_supabase_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> Dict[str, Any]:
    """Verify Supabase JWT token and return user info"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Verify token with Supabase
        token = credentials.credentials
        user_response = supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "metadata": user.user_metadata
        }
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_info: Dict[str, Any] = Depends(verify_supabase_token)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    return user_info


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: Client = Depends(get_supabase)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await verify_supabase_token(credentials, supabase)
    except HTTPException:
        return None


def require_role(required_role: str):
    """Dependency factory for role-based access control"""
    async def role_checker(
        user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        user_role = user.get("role", "user")
        
        # Role hierarchy: admin > moderator > user
        role_hierarchy = {"user": 0, "moderator": 1, "admin": 2}
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        
        return user
    
    return role_checker


# Convenience dependencies
require_admin = require_role("admin")
require_moderator = require_role("moderator")
