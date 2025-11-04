"""
=============================================================================
JARVIS 3.0 - PATTERN MODEL (Pydantic Schemas for Pattern Detection)
=============================================================================

PURPOSE:
--------
Defines Pydantic data models for patterns detected by PatternDetectorAgent (Day 3).
Patterns represent correlations, trends, and anomalies discovered in user event data
(e.g., "Workout days → 85% more tasks completed").

RESPONSIBILITY:
---------------
- Define pattern data structure with confidence scores
- Track pattern frequency (how many times observed)
- Store correlation metadata (sample size, coefficients)
- Validate pattern types (correlation, trend, anomaly)
- Provide schemas for pattern storage and retrieval

DATA FLOW (Pattern Detection → Storage → Retrieval):
-----------------------------------------------------
PATTERN DETECTION FLOW (Day 3):
1. PatternDetectorAgent analyzes events from jarvis_events.db
2. Runs statistical analysis (correlation, regression, frequency counting)
3. Finds significant pattern: "Workout → Task completion correlation: 0.85"
4. Create Pattern object with:
   - pattern_type: "correlation"
   - description: "Workout days → 85% more tasks completed"
   - confidence: 0.85
   - data: {"event_a": "workout", "event_b": "task", "coefficient": 0.85}
5. Call jarvis_db.create_pattern(pattern_data)
6. Store in patterns table

PATTERN RETRIEVAL FLOW:
1. Client requests GET /api/patterns (Day 3 endpoint)
2. simple_main.py calls jarvis_db.get_patterns(user_id)
3. Convert SQLite rows to PatternResponse models
4. Return JSON array of patterns sorted by confidence

PATTERN UPDATE FLOW:
1. PatternDetectorAgent re-detects existing pattern
2. Increment frequency counter
3. Update last_seen timestamp
4. Recalculate confidence score with new data

PATTERN TYPES:
--------------
1. "correlation": Event A → Event B relationship (workout → task completion)
2. "trend": Time-based patterns (declining energy over week)
3. "anomaly": Unusual deviations (sudden drop in activity)

EXAMPLE PATTERNS:
-----------------
Correlation Pattern:
{
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

Trend Pattern:
{
  "pattern_type": "trend",
  "description": "Energy declining over past 2 weeks",
  "confidence": 0.72,
  "frequency": 14,
  "data": {
    "metric": "energy_level",
    "slope": -0.3,
    "period_days": 14
  }
}

Anomaly Pattern:
{
  "pattern_type": "anomaly",
  "description": "Sudden drop in meditation frequency",
  "confidence": 0.90,
  "frequency": 1,
  "data": {
    "baseline_avg": 5.2,
    "current_avg": 1.3,
    "deviation_std": 3.1
  }
}

DEPENDENCIES:
-------------
- pydantic: BaseModel, Field for validation
- datetime: Timestamp fields for first_detected, last_seen

USED BY:
--------
- agents/pattern_detector.py: Pattern creation (Day 3)
- simple_main.py: Pattern API endpoints (Day 3)
- simple_jarvis_db.py: Pattern database operations
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
