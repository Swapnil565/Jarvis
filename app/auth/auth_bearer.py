"""
JWT Bearer authentication for JARVIS 3.0 Backend
FastAPI dependency for protecting endpoints with JWT tokens
"""

from typing import Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .auth_handler import verify_token, get_user_id_from_token
from ..core.database import get_db
from ..models.user import User


class JWTBearer(HTTPBearer):
    """
    JWT Bearer token authentication dependency
    Validates JWT tokens and extracts user information
    """
    
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> str:
        """
        Validate JWT token from Authorization header
        
        Args:
            request: FastAPI request object
            
        Returns:
            Valid JWT token string
            
        Raises:
            HTTPException: If token is invalid or missing
        """
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme. Use Bearer token."
                )
            
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired token."
                )
            
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )
    
    def verify_jwt(self, token: str) -> bool:
        """
        Verify if JWT token is valid
        
        Args:
            token: JWT token to verify
            
        Returns:
            True if token is valid, False otherwise
        """
        payload = verify_token(token)
        return payload is not None


# Dependency functions for different authentication levels

async def get_current_user_token(token: str = Depends(JWTBearer())) -> str:
    """
    Dependency to get current user's valid token
    
    Args:
        token: JWT token from JWTBearer dependency
        
    Returns:
        Valid JWT token string
    """
    return token


async def get_current_user_id(token: str = Depends(JWTBearer())) -> int:
    """
    Dependency to get current user's ID from token
    
    Args:
        token: JWT token from JWTBearer dependency
        
    Returns:
        User ID extracted from token
        
    Raises:
        HTTPException: If user ID cannot be extracted
    """
    user_id = get_user_id_from_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current user object from database
    
    Args:
        user_id: User ID from get_current_user_id dependency
        db: Database session from get_db dependency
        
    Returns:
        User object from database
        
    Raises:
        HTTPException: If user not found or inactive
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get current active user
    
    Args:
        current_user: User object from get_current_user dependency
        
    Returns:
        Active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


class OptionalJWTBearer(JWTBearer):
    """
    Optional JWT Bearer authentication
    Allows endpoints to work with or without authentication
    """
    
    def __init__(self):
        super(OptionalJWTBearer, self).__init__(auto_error=False)
    
    async def __call__(self, request: Request) -> Optional[str]:
        """
        Optionally validate JWT token
        
        Args:
            request: FastAPI request object
            
        Returns:
            Valid JWT token string or None if not provided
        """
        try:
            credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
            
            if credentials and credentials.scheme == "Bearer":
                if self.verify_jwt(credentials.credentials):
                    return credentials.credentials
            
            return None
        except HTTPException:
            return None


async def get_optional_current_user(
    token: Optional[str] = Depends(OptionalJWTBearer()),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get current user
    
    Args:
        token: Optional JWT token
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    if token is None:
        return None
    
    user_id = get_user_id_from_token(token)
    if user_id is None:
        return None
    
    try:
        user_id = int(user_id)
        user = db.query(User).filter(User.id == user_id).first()
        return user if user and user.is_active else None
    except (ValueError, TypeError):
        return None


# Security dependencies for different user roles

async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure current user is an admin
    
    Args:
        current_user: Current active user
        
    Returns:
        Admin user object
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Add admin check logic here when user roles are implemented
    # For now, we'll use is_premium as a placeholder for admin status
    if not getattr(current_user, 'is_premium', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user


async def get_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to ensure current user is verified
    
    Args:
        current_user: Current active user
        
    Returns:
        Verified user object
        
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user
