"""
Authentication handler for JARVIS 3.0 Backend
Handles password hashing, JWT token creation/validation, and user authentication
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, status

from ..core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time (optional)
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create access token: {str(e)}"
        )


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration
    
    Args:
        data: Data to encode in the token
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    to_encode.update({"exp": expire, "type": "refresh"})
    
    try:
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create refresh token: {str(e)}"
        )


def decode_jwt(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        return None


def verify_token(token: str) -> Optional[dict]:
    """
    Verify a JWT token and extract payload
    
    Args:
        token: JWT token to verify
        
    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token has expired
        exp = payload.get("exp")
        if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
            
        return payload
    except JWTError:
        return None


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from JWT token
    
    Args:
        token: JWT token containing user information
        
    Returns:
        User ID if token is valid, None otherwise
    """
    payload = verify_token(token)
    if payload:
        return payload.get("sub")  # 'sub' is the standard JWT claim for user ID
    return None


class AuthHandler:
    """
    Main authentication handler class
    Provides a centralized interface for all authentication operations
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return hash_password(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return verify_password(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(user_id: int, additional_data: dict = None) -> str:
        """Create access token for user"""
        data = {"sub": str(user_id)}
        if additional_data:
            data.update(additional_data)
        return create_access_token(data)
    
    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        """Create refresh token for user"""
        data = {"sub": str(user_id)}
        return create_refresh_token(data)
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """Verify a token and return payload"""
        return verify_token(token)
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[int]:
        """Get user ID from token"""
        return get_user_id_from_token(token)
    
    @staticmethod
    def create_tokens_for_user(user_id: int) -> dict:
        """Create both access and refresh tokens for a user"""
        access_token = AuthHandler.create_access_token(user_id)
        refresh_token = AuthHandler.create_refresh_token(user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }
