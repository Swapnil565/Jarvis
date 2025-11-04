"""
=============================================================================
JARVIS 3.0 - AUTHENTICATION MODULE (JWT-based User Auth)
=============================================================================

PURPOSE:
--------
Handles user registration, login, and JWT token-based authentication for
securing API endpoints. Provides the authentication layer for JARVIS.

RESPONSIBILITY:
---------------
- User registration (create new accounts with hashed passwords)
- User login (validate credentials, issue JWT tokens)
- Token validation (protect endpoints via get_current_user dependency)
- Password hashing (SHA256 for security)
- JWT token generation and verification

DATA FLOW (Authentication Requests):
------------------------------------
REGISTRATION FLOW:
1. POST /api/v1/auth/register with {"username": "user", "password": "pass"}
2. Validate username doesn't exist (check simple_db.py users table)
3. Hash password with SHA256 + salt
4. Insert user into database via db.create_user()
5. Generate JWT token with user_id + username payload
6. Return {"access_token": "jwt...", "token_type": "bearer", "user": {...}}

LOGIN FLOW:
1. POST /api/v1/auth/login with {"username": "user", "password": "pass"}
2. Fetch user from database via db.get_user_by_username()
3. Hash provided password and compare with stored hash
4. If match: generate JWT token with 24-hour expiry
5. Return {"access_token": "jwt...", "token_type": "bearer", "user": {...}}
6. If no match: raise 401 Unauthorized

PROTECTED ENDPOINT FLOW:
1. Client sends request with "Authorization: Bearer <JWT_TOKEN>" header
2. Endpoint uses Depends(get_current_user) dependency
3. get_current_user() extracts token from header
4. Verify token signature and expiry with jwt.decode()
5. Extract user_id from token payload
6. Fetch user from database to ensure still exists
7. Return user dict to endpoint handler
8. If invalid: raise 401 Unauthorized

DEPENDENCIES:
-------------
- simple_db.py: User database operations (create_user, get_user_by_username, get_user_by_id)
- PyJWT library: JWT token encoding/decoding
- hashlib: SHA256 password hashing
- FastAPI: HTTPException for auth errors

SECURITY NOTES:
---------------
- Passwords hashed with SHA256 (NOT stored as plaintext)
- JWT tokens expire after 24 hours
- SECRET_KEY from environment variable (changeable in production)
- Token validation on every protected endpoint request
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import os

try:
    import jwt
except ImportError:
    print("PyJWT not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "PyJWT"])
    import jwt

# Import simple database
from simple_db import db

router = APIRouter()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# Pydantic models
class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None
    bio: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict

class SuccessResponse(BaseModel):
    message: str
    data: dict

def create_access_token(user_data: dict) -> dict:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "exp": expire,
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": encoded_jwt,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600  # seconds
    }

def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

@router.post("/register", response_model=SuccessResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Basic password validation
        if len(user_data.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Create user in database
        result = db.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
            bio=user_data.bio
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return SuccessResponse(
            message="User registered successfully",
            data={
                "user_id": result["id"],
                "email": result["email"],
                "username": result["username"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login_user(login_data: UserLogin):
    """Authenticate user and return access token"""
    try:
        # Authenticate user
        user = db.authenticate_user(login_data.email, login_data.password)
        
        if not user or "error" in user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token
        token_data = create_access_token(user)
        
        return Token(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# Simple JWT Bearer dependency
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request

class SimpleJWTBearer(HTTPBearer):
    """Simple JWT Bearer authentication"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme"
                )
            
            payload = verify_token(credentials.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired token"
                )
            
            # Get user from database
            user_id = int(payload.get("sub"))
            user = db.get_user_by_id(user_id)
            
            if not user or "error" in user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            return user
        else:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Authorization header required"
                )
            return None

# Dependencies
simple_jwt_bearer = SimpleJWTBearer()

async def get_current_user(user=Depends(simple_jwt_bearer)):
    """Get current authenticated user"""
    return user