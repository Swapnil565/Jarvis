"""
Security utilities for JARVIS 3.0 Backend
Additional security functions for password validation, token management, etc.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from fastapi import HTTPException, status

from .auth_handler import hash_password as _hash_password, verify_password as _verify_password

# Re-export main functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return _verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return _hash_password(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token - wrapper for auth_handler function"""
    from .auth_handler import create_access_token as _create_access_token
    return _create_access_token(data, expires_delta)


# Additional security utilities

def generate_random_password(length: int = 12) -> str:
    """
    Generate a secure random password
    
    Args:
        length: Length of the password to generate
        
    Returns:
        Randomly generated password string
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_reset_token() -> str:
    """
    Generate a secure token for password reset
    
    Returns:
        Secure random token string
    """
    return secrets.token_urlsafe(32)


def generate_verification_token() -> str:
    """
    Generate a secure token for email verification
    
    Returns:
        Secure random token string
    """
    return secrets.token_urlsafe(32)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and return detailed feedback
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results and feedback
    """
    result = {
        "is_valid": True,
        "score": 0,
        "feedback": [],
        "requirements_met": {
            "min_length": False,
            "has_uppercase": False,
            "has_lowercase": False,
            "has_digit": False,
            "has_special": False
        }
    }
    
    # Check minimum length
    if len(password) >= 8:
        result["requirements_met"]["min_length"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must be at least 8 characters long")
    
    # Check for uppercase letter
    if any(c.isupper() for c in password):
        result["requirements_met"]["has_uppercase"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one uppercase letter")
    
    # Check for lowercase letter
    if any(c.islower() for c in password):
        result["requirements_met"]["has_lowercase"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one lowercase letter")
    
    # Check for digit
    if any(c.isdigit() for c in password):
        result["requirements_met"]["has_digit"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one digit")
    
    # Check for special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if any(c in special_chars for c in password):
        result["requirements_met"]["has_special"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one special character")
    
    # Check for common weak patterns
    weak_patterns = [
        "password", "123456", "qwerty", "admin", "user", "guest",
        "welcome", "login", "abc123", "password123"
    ]
    
    if password.lower() in weak_patterns:
        result["feedback"].append("Password is too common and easily guessable")
        result["score"] = max(0, result["score"] - 2)
    
    # Determine if password is valid (at least 4 out of 5 requirements)
    result["is_valid"] = result["score"] >= 4
    
    return result


def check_password_requirements(password: str) -> bool:
    """
    Check if password meets minimum security requirements
    
    Args:
        password: Password to check
        
    Returns:
        True if password meets requirements, False otherwise
        
    Raises:
        HTTPException: If password doesn't meet requirements
    """
    validation = validate_password_strength(password)
    
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Password does not meet security requirements",
                "feedback": validation["feedback"],
                "requirements": validation["requirements_met"]
            }
        )
    
    return True


class SecurityManager:
    """
    Centralized security management class
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password with security validation"""
        check_password_requirements(password)
        return get_password_hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return verify_password(plain_password, hashed_password)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        return validate_password_strength(password)
    
    @staticmethod
    def create_password_reset_token() -> Dict[str, Any]:
        """Create password reset token with expiration"""
        token = generate_reset_token()
        expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
        
        return {
            "token": token,
            "expires_at": expires_at,
            "type": "password_reset"
        }
    
    @staticmethod
    def create_email_verification_token() -> Dict[str, Any]:
        """Create email verification token with expiration"""
        token = generate_verification_token()
        expires_at = datetime.utcnow() + timedelta(days=1)  # 24 hour expiration
        
        return {
            "token": token,
            "expires_at": expires_at,
            "type": "email_verification"
        }
    
    @staticmethod
    def is_token_expired(expires_at: datetime) -> bool:
        """Check if a token has expired"""
        return datetime.utcnow() > expires_at


# Rate limiting utilities (for future implementation)

class RateLimiter:
    """
    Simple rate limiting class
    """
    
    def __init__(self):
        self._attempts = {}
    
    def is_rate_limited(self, identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> bool:
        """
        Check if an identifier (IP, user ID, etc.) is rate limited
        
        Args:
            identifier: Unique identifier to track
            max_attempts: Maximum attempts allowed
            window_minutes: Time window in minutes
            
        Returns:
            True if rate limited, False otherwise
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old attempts
        if identifier in self._attempts:
            self._attempts[identifier] = [
                attempt for attempt in self._attempts[identifier]
                if attempt > window_start
            ]
        
        # Check current attempts
        current_attempts = len(self._attempts.get(identifier, []))
        return current_attempts >= max_attempts
    
    def record_attempt(self, identifier: str):
        """Record an attempt for rate limiting"""
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        
        self._attempts[identifier].append(datetime.utcnow())


# Global rate limiter instance
rate_limiter = RateLimiter()
