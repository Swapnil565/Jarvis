"""
User model for JARVIS 3.0 Backend
Handles user authentication and profile management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from ..core.database import Base


class User(Base):
    """SQLAlchemy User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Profile information
    bio = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string
    
    # Status flags
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    conversations = relationship("Conversation", back_populates="user")


# Pydantic models for API serialization
class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserUpdate(BaseModel):
    """User update model"""
    full_name: Optional[str] = None
    bio: Optional[str] = None
    preferences: Optional[str] = None


class UserResponse(UserBase):
    """User response model"""
    id: int
    is_active: bool
    is_verified: bool
    is_premium: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    """Extended user profile model"""
    id: int
    email: str
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    is_premium: bool
    created_at: datetime
    total_documents: int = 0
    total_conversations: int = 0
    
    class Config:
        orm_mode = True


class TokenData(BaseModel):
    """Token data model"""
    email: Optional[str] = None
    user_id: Optional[int] = None


class Token(BaseModel):
    """Authentication token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse