"""
Event Model for Bible JARVIS - Tracks physical, mental, and spiritual events
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class EventCategory(str, Enum):
    """Event categories matching the 3 dimensions of Bible JARVIS"""
    PHYSICAL = "physical"
    MENTAL = "mental"
    SPIRITUAL = "spiritual"


class Event(BaseModel):
    """
    Event model for tracking user activities across 3 dimensions
    
    Examples:
    - PHYSICAL: Workout, Sleep, Meal, Energy levels
    - MENTAL: Task completed, Work session, Focus time, Overwhelm
    - SPIRITUAL: Meditation, Prayer, Reflection, Gratitude
    """
    id: Optional[int] = None
    user_id: int
    category: EventCategory
    event_type: str  # e.g., "workout", "task", "meditation"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    feeling: Optional[str] = None  # e.g., "energized", "tired", "calm", "stressed"
    data: Dict[str, Any] = {}  # Flexible JSONB-like storage for event-specific data
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "category": "physical",
                "event_type": "workout",
                "timestamp": "2025-06-15T07:30:00",
                "feeling": "energized",
                "data": {
                    "duration_minutes": 45,
                    "type": "strength_training",
                    "intensity": "high"
                }
            }
        }


class EventCreate(BaseModel):
    """Schema for creating a new event"""
    category: EventCategory
    event_type: str
    feeling: Optional[str] = None
    data: Dict[str, Any] = {}


class EventResponse(BaseModel):
    """Schema for event API responses"""
    id: int
    user_id: int
    category: EventCategory
    event_type: str
    timestamp: datetime
    feeling: Optional[str]
    data: Dict[str, Any]
