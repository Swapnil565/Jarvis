"""
Pattern Model for Bible JARVIS - Stores detected correlations and patterns
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class Pattern(BaseModel):
    """
    Pattern model for storing detected correlations
    
    Examples:
    - "Workout days → 85% more tasks completed"
    - "Less than 6h sleep → 3x more overwhelm reports"
    - "Morning meditation → 40% calmer day"
    """
    id: Optional[int] = None
    user_id: int
    pattern_type: str  # e.g., "correlation", "trend", "anomaly"
    description: str  # Human-readable pattern description
    confidence: float = Field(ge=0.0, le=1.0)  # Confidence score 0-1
    frequency: int = 1  # How many times this pattern has been observed
    first_detected: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = {}  # Pattern-specific data (correlation coefficients, etc.)
    is_active: bool = True  # Whether this pattern is still relevant
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "pattern_type": "correlation",
                "description": "Workout days → 85% more tasks completed",
                "confidence": 0.85,
                "frequency": 12,
                "data": {
                    "event_a": "workout",
                    "event_b": "task_completed",
                    "correlation_coefficient": 0.85,
                    "sample_size": 30
                }
            }
        }


class PatternResponse(BaseModel):
    """Schema for pattern API responses"""
    id: int
    user_id: int
    pattern_type: str
    description: str
    confidence: float
    frequency: int
    first_detected: datetime
    last_seen: datetime
    data: Dict[str, Any]
    is_active: bool
