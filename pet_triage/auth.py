"""
Authentication Module
=====================

Simple JWT-based authentication with no token expiry.
Uses SQLite database for user storage.

Features:
- Email/password registration
- Password hashing with bcrypt
- JWT token generation (no expiry)
- Token verification
"""

import os
import jwt
import bcrypt
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# Import database functions
from database import (
    create_user as db_create_user,
    get_user_by_email as db_get_user_by_email,
    get_user_by_id as db_get_user_by_id,
    get_pet_profile as db_get_pet_profile
)

# JWT secret key (in production, use environment variable)
JWT_SECRET = os.getenv("JWT_SECRET", "fuzzy-friend-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"


# =============================================================================
# Pydantic Models
# =============================================================================

class UserRegister(BaseModel):
    """Registration request model."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data returned to client (no password)."""
    id: str
    name: str
    email: str
    created_at: str
    has_pet_profile: bool = False


class AuthResponse(BaseModel):
    """Authentication response with token."""
    success: bool
    token: Optional[str] = None
    user: Optional[UserResponse] = None
    pet_profile: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# =============================================================================
# Password Hashing
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# =============================================================================
# JWT Token Management
# =============================================================================

def create_token(user_id: str, email: str, name: str) -> str:
    """
    Create a JWT token with no expiry.
    
    Payload contains:
    - sub: user_id
    - email: user's email
    - name: user's name
    - iat: issued at timestamp
    """
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "iat": datetime.utcnow().timestamp()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return the payload.
    Returns None if token is invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        return None


# =============================================================================
# Auth Functions
# =============================================================================

def register_user(name: str, email: str, password: str) -> AuthResponse:
    """
    Register a new user.
    
    Returns AuthResponse with token on success.
    """
    # Check if user already exists
    if db_get_user_by_email(email):
        return AuthResponse(success=False, error="Email already registered")
    
    # Create user
    user_id = f"user_{int(datetime.utcnow().timestamp())}"
    created_at = datetime.utcnow().isoformat()
    
    success = db_create_user(
        user_id=user_id,
        email=email.lower().strip(),
        password_hash=hash_password(password),
        name=name.strip()
    )
    
    if not success:
        return AuthResponse(success=False, error="Email already registered")
    
    # Generate token
    token = create_token(user_id, email.lower().strip(), name.strip())
    
    return AuthResponse(
        success=True,
        token=token,
        user=UserResponse(
            id=user_id,
            name=name.strip(),
            email=email.lower().strip(),
            created_at=created_at,
            has_pet_profile=False
        )
    )


def login_user(email: str, password: str) -> AuthResponse:
    """
    Authenticate a user.
    
    Returns AuthResponse with token and pet profile on success.
    """
    user = db_get_user_by_email(email)
    
    if not user:
        return AuthResponse(success=False, error="Invalid email or password")
    
    if not verify_password(password, user.get("password_hash", "")):
        return AuthResponse(success=False, error="Invalid email or password")
    
    # Generate token
    token = create_token(user["id"], user["email"], user["name"])
    
    # Get pet profile if exists
    pet_profile = db_get_pet_profile(user["id"])
    
    return AuthResponse(
        success=True,
        token=token,
        user=UserResponse(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            created_at=user.get("created_at", ""),
            has_pet_profile=pet_profile is not None
        ),
        pet_profile=pet_profile
    )


def get_current_user(token: str) -> Optional[UserResponse]:
    """
    Get current user from token.
    
    Returns UserResponse if token is valid, None otherwise.
    """
    payload = verify_token(token)
    if not payload:
        return None
    
    user = db_get_user_by_email(payload.get("email", ""))
    if not user:
        return None
    
    pet_profile = db_get_pet_profile(user["id"])
    
    return UserResponse(
        id=user["id"],
        name=user["name"],
        email=user["email"],
        created_at=user.get("created_at", ""),
        has_pet_profile=pet_profile is not None
    )
