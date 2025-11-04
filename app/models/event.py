"""
=============================================================================
JARVIS 3.0 - EVENT MODEL (Pydantic Schemas for Event Validation)
=============================================================================

PURPOSE:
--------
Defines Pydantic data models for event validation and serialization. These
schemas ensure data integrity between API requests, database operations, and
API responses. Acts as the CONTRACT for event data structure.

RESPONSIBILITY:
---------------
- Define EventCategory enum (physical, mental, spiritual)
- Validate event data structure with type checking
- Provide schemas for CREATE operations (EventCreate)
- Provide schemas for READ operations (EventResponse)
- Document expected data formats with examples
- Ensure consistency across entire codebase

DATA FLOW (Request → Database → Response):
-------------------------------------------
REQUEST VALIDATION FLOW:
1. Client sends POST /api/events with JSON body
2. FastAPI automatically validates against EventCreate schema
3. If invalid (missing fields, wrong types): return 422 Unprocessable Entity
4. If valid: pass validated data to endpoint handler

DATABASE INSERTION FLOW:
1. simple_main.py receives validated EventCreate object
2. Extract fields: category, event_type, feeling, data
3. Pass to jarvis_db.create_event()
4. Database stores with auto-generated id and timestamp

RESPONSE SERIALIZATION FLOW:
1. jarvis_db returns event dict from SQLite
2. simple_main.py converts to EventResponse Pydantic model
3. FastAPI automatically serializes to JSON
4. Client receives JSON with all fields typed correctly

SCHEMA TYPES:
-------------
1. Event: Complete model with all fields (used internally)
2. EventCreate: Input schema for POST requests (no id/timestamp)
3. EventResponse: Output schema for GET requests (includes id/timestamp)
4. EventCategory: Enum restricting category to 3 values

EXAMPLE DATA:
-------------
Physical Event:
{
  "category": "physical",
  "event_type": "workout",
  "feeling": "energized",
  "data": {
    "workout_type": "upper_body",
    "intensity": "heavy",
    "duration": 60
  }
}

Mental Event:
{
  "category": "mental",
  "event_type": "task",
  "feeling": "focused",
  "data": {
    "title": "client proposal",
    "completed": true,
    "priority": "high"
  }
}

Spiritual Event:
{
  "category": "spiritual",
  "event_type": "meditation",
  "feeling": "calm",
  "data": {
    "duration": 10,
    "method": "breathing"
  }
}

DEPENDENCIES:
-------------
- pydantic: BaseModel, Field for validation
- datetime: Timestamp fields
- enum: EventCategory enum
- typing: Type hints for Dict, Optional

USED BY:
--------
- simple_main.py: Endpoint request/response validation
- agents/data_collector.py: Parse output validation
- simple_jarvis_db.py: Database operation type hints
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
