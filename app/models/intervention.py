"""
Intervention Model for Bible JARVIS - Proactive suggestions and interventions
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class InterventionType(str, Enum):
    """Types of interventions Bible JARVIS can suggest"""
    WARNING = "warning"  # "You're overtraining, rest day needed"
    SUGGESTION = "suggestion"  # "Good time for meditation"
    INSIGHT = "insight"  # "You work best after morning workouts"
    FORECAST = "forecast"  # "Energy debt building, crash predicted in 3 days"


class InterventionUrgency(str, Enum):
    """Urgency levels for interventions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Intervention(BaseModel):
    """
    Intervention model for proactive suggestions
    
    Examples:
    - WARNING: "You've worked 12 days straight without a break. Burnout risk: HIGH"
    - SUGGESTION: "Your energy is 20% above baseline. Good time to tackle that hard task"
    - INSIGHT: "You complete 2x more tasks after morning meditation"
    - FORECAST: "Energy debt building. Predicted crash: Thursday"
    """
    id: Optional[int] = None
    user_id: int
    intervention_type: InterventionType
    urgency: InterventionUrgency = InterventionUrgency.MEDIUM
    title: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)  # User feedback 1-5 stars
    was_helpful: Optional[bool] = None
    data: Dict[str, Any] = {}  # Supporting data (pattern IDs, forecasts, etc.)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "intervention_type": "warning",
                "urgency": "high",
                "title": "Overtraining Detected",
                "message": "You've worked out 7 days straight. Rest day strongly recommended to prevent burnout.",
                "data": {
                    "consecutive_workout_days": 7,
                    "fatigue_score": 8.5,
                    "recovery_time_needed": "48h"
                }
            }
        }


class InterventionCreate(BaseModel):
    """Schema for creating interventions"""
    intervention_type: InterventionType
    urgency: InterventionUrgency
    title: str
    message: str
    data: Dict[str, Any] = {}


class InterventionResponse(BaseModel):
    """Schema for intervention API responses"""
    id: int
    user_id: int
    intervention_type: InterventionType
    urgency: InterventionUrgency
    title: str
    message: str
    created_at: datetime
    delivered_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    user_rating: Optional[int]
    was_helpful: Optional[bool]
    data: Dict[str, Any]


class InterventionFeedback(BaseModel):
    """Schema for user feedback on interventions"""
    rating: int = Field(ge=1, le=5)
    was_helpful: bool
