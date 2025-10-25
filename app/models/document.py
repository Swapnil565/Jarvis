"""
Document model for JARVIS 3.0 Backend
Handles document storage and vector embeddings
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..core.database import Base


class Document(Base):
    """SQLAlchemy Document model"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Vector embeddings
    embedding = Column(ARRAY(Float), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    
    # Metadata
    tags = Column(ARRAY(String), nullable=True)
    category = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    
    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Relationships
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="documents")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)


# Pydantic models for API serialization
class DocumentBase(BaseModel):
    """Base document model"""
    title: str
    content: str
    file_type: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    language: str = "en"


class DocumentCreate(DocumentBase):
    """Document creation model"""
    pass


class DocumentUpdate(BaseModel):
    """Document update model"""
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Document response model"""
    id: int
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    processing_status: str
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class DocumentUpload(BaseModel):
    """Document upload model"""
    title: str
    file_data: bytes
    file_name: str
    file_type: str
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class DocumentSearch(BaseModel):
    """Document search model"""
    query: str
    limit: int = 10
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    similarity_threshold: float = 0.5


class DocumentSearchResult(BaseModel):
    """Document search result model"""
    document: DocumentResponse
    similarity_score: float
    matched_content: str


class DocumentStats(BaseModel):
    """Document statistics model"""
    total_documents: int
    total_size: int
    by_category: dict
    by_file_type: dict
    processing_status: dict