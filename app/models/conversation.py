"""
Conversation model for JARVIS 3.0 Backend
Handles chat conversations and message history
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ..core.database import Base


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base):
    """SQLAlchemy Conversation model"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    
    # Conversation metadata
    context_data = Column(JSON, nullable=True)  # Store conversation context
    settings = Column(JSON, nullable=True)  # Conversation-specific settings
    
    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), nullable=True)


class Message(Base):
    """SQLAlchemy Message model"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    
    # Message metadata
    metadata = Column(JSON, nullable=True)  # Additional message data
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    # Relationships
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    conversation = relationship("Conversation", back_populates="messages")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Pydantic models for API serialization
class MessageBase(BaseModel):
    """Base message model"""
    content: str
    role: MessageRole


class MessageCreate(MessageBase):
    """Message creation model"""
    conversation_id: int


class MessageResponse(MessageBase):
    """Message response model"""
    id: int
    conversation_id: int
    metadata: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime
    
    class Config:
        orm_mode = True


class ConversationBase(BaseModel):
    """Base conversation model"""
    title: str


class ConversationCreate(ConversationBase):
    """Conversation creation model"""
    context_data: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """Conversation update model"""
    title: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_archived: Optional[bool] = None


class ConversationResponse(ConversationBase):
    """Conversation response model"""
    id: int
    user_id: int
    context_data: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: bool
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None
    message_count: int = 0
    
    class Config:
        orm_mode = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with messages included"""
    messages: List[MessageResponse] = []


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    message: MessageResponse
    conversation: ConversationResponse
    processing_info: Optional[Dict[str, Any]] = None


class ConversationStats(BaseModel):
    """Conversation statistics model"""
    total_conversations: int
    active_conversations: int
    archived_conversations: int
    total_messages: int
    avg_messages_per_conversation: float
    total_tokens_used: int