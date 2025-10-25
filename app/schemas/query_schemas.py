"""
Query and response schemas for JARVIS 3.0 Backend
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Query request model"""
    query: str = Field(description="User query to process")
    context: Dict[str, Any] = Field(default={}, description="Additional context for the query")
    conversation_id: Optional[int] = Field(default=None, description="Conversation ID for context")
    user_preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")


class QueryResponse(BaseModel):
    """Query response model"""
    response: str = Field(description="AI response to the query")
    status: str = Field(description="Processing status")
    query_analysis: Dict[str, Any] = Field(default={}, description="Analysis of the query")
    processing_time_ms: float = Field(description="Processing time in milliseconds")
    sources: Optional[list] = Field(default=None, description="Sources used for the response")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(description="Search query")
    search_type: str = Field(default="semantic", description="Type of search (semantic, keyword, hybrid)")
    limit: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters")


class SearchResult(BaseModel):
    """Search result model"""
    document_id: int
    title: str
    content: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None