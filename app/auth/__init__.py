"""
Authentication module for JARVIS 3.0 Backend
Contains JWT authentication, security, and authorization utilities
"""

from .auth_handler import AuthHandler, create_access_token, verify_token, hash_password, verify_password
from .auth_bearer import JWTBearer, get_current_user, get_current_user_id, OptionalJWTBearer
from .security import (
    get_password_hash, SecurityManager, check_password_requirements,
    validate_password_strength, generate_random_password
)

__all__ = [
    # Auth Handler
    "AuthHandler",
    "create_access_token",
    "verify_token",
    "hash_password", 
    "verify_password",
    
    # Auth Bearer & Dependencies
    "JWTBearer",
    "get_current_user",
    "get_current_user_id",
    "OptionalJWTBearer",
    
    # Security utilities
    "get_password_hash",
    "SecurityManager",
    "check_password_requirements",
    "validate_password_strength",
    "generate_random_password"
]