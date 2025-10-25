"""
Authentication endpoints for JARVIS 3.0 Backend
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...schemas.base_schemas import SuccessResponse, ErrorResponse
from ...models.user import User, UserLogin, UserCreate, UserResponse, Token
from ...auth.auth_handler import AuthHandler
from ...auth.security import SecurityManager, check_password_requirements

router = APIRouter()


async def get_user_by_email(email: str, db: Session) -> User:
    """Get user by email from database"""
    return db.query(User).filter(User.email == email).first()


async def create_user_in_db(user_data: UserCreate, db: Session) -> User:
    """Create a new user in the database"""
    hashed_password = SecurityManager.hash_password(user_data.password)
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        bio=user_data.bio,
        is_active=True,
        is_verified=False,  # Email verification required
        created_at=datetime.utcnow()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/register", response_model=SuccessResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: Valid email address (must be unique)
    - **username**: Unique username
    - **password**: Strong password meeting security requirements
    - **full_name**: User's full name (optional)
    - **bio**: User bio (optional)
    """
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(user_data.email, db)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username is taken
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Validate password strength
        check_password_requirements(user_data.password)
        
        # Create user
        user = await create_user_in_db(user_data, db)
        
        # Generate verification token (for future email verification)
        verification_token = SecurityManager.create_email_verification_token()
        
        return SuccessResponse(
            message="User registered successfully. Please check your email for verification.",
            data={
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "verification_required": True
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
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token
    
    - **email**: User's registered email
    - **password**: User's password
    
    Returns JWT access token and refresh token
    """
    try:
        # Get user from database
        user = await get_user_by_email(login_data.email, db)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not SecurityManager.verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is disabled"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create tokens
        token_data = AuthHandler.create_tokens_for_user(user.id)
        
        # Create user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_premium=user.is_premium,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return Token(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh authentication token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and refresh token
    """
    try:
        # Verify refresh token
        payload = AuthHandler.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = AuthHandler.create_tokens_for_user(user.id)
        
        # Create user response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_premium=user.is_premium,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return Token(
            access_token=token_data["access_token"],
            token_type=token_data["token_type"],
            expires_in=token_data["expires_in"],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout_user():
    """
    Logout user and invalidate token
    
    Note: In a stateless JWT system, logout is handled client-side by discarding the token.
    For enhanced security, implement token blacklisting in a future version.
    """
    return SuccessResponse(
        message="Logged out successfully. Please discard your access token.",
        data={"logged_out": True}
    )


@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    verification_token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user email address using verification token
    
    - **verification_token**: Email verification token sent to user's email
    """
    # TODO: Implement email verification logic
    # This would involve storing verification tokens in database
    # and updating user.is_verified when token is valid
    
    return SuccessResponse(
        message="Email verification endpoint - implementation pending",
        data={"verification_token": verification_token}
    )


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Request password reset for user
    
    - **email**: User's registered email address
    """
    try:
        user = await get_user_by_email(email, db)
        
        if user:
            # Generate password reset token
            reset_token = SecurityManager.create_password_reset_token()
            
            # TODO: Store reset token in database and send email
            # For now, just return success message
            
            return SuccessResponse(
                message="If the email exists in our system, a password reset link has been sent.",
                data={"email": email}
            )
        else:
            # Don't reveal if email exists for security
            return SuccessResponse(
                message="If the email exists in our system, a password reset link has been sent.",
                data={"email": email}
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}"
        )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    reset_token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Reset user password using reset token
    
    - **reset_token**: Password reset token from email
    - **new_password**: New password meeting security requirements
    """
    try:
        # Validate new password
        check_password_requirements(new_password)
        
        # TODO: Implement password reset logic
        # This would involve verifying the reset token and updating user password
        
        return SuccessResponse(
            message="Password reset endpoint - implementation pending",
            data={"reset_token": reset_token[:10] + "..."}  # Partially hide token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )