"""
=============================================================================
JARVIS 3.0 - MODELS PACKAGE (Pydantic Data Schemas)
=============================================================================

PURPOSE:
--------
Package entry point for all Pydantic data models. Provides clean imports for
event, pattern, and intervention schemas used throughout the application.
These models ensure type safety and data validation at API boundaries.

MODELS HIERARCHY:
-----------------
1. EVENT MODELS (event.py):
   - Event: Complete event model with all fields
   - EventCreate: Input schema for creating events (POST requests)
   - EventResponse: Output schema for returning events (GET responses)
   - EventCategory: Enum for physical/mental/spiritual

2. PATTERN MODELS (pattern.py):
   - Pattern: Complete pattern model with confidence scores
   - PatternResponse: Output schema for pattern API responses

3. INTERVENTION MODELS (intervention.py):
   - Intervention: Complete intervention model with urgency levels
   - InterventionCreate: Input schema for creating interventions
   - InterventionResponse: Output schema for intervention API responses
   - InterventionFeedback: User feedback schema (rating, was_helpful)
   - InterventionType: Enum for warning/suggestion/insight/forecast
   - InterventionUrgency: Enum for low/medium/high/critical

DATA FLOW (Models at API Boundaries):
--------------------------------------
REQUEST FLOW:
1. Client sends JSON to POST /api/events
2. FastAPI deserializes → EventCreate Pydantic model
3. Automatic validation (type checking, required fields)
4. If invalid: 422 Unprocessable Entity with error details
5. If valid: Pass to endpoint handler

RESPONSE FLOW:
1. Database returns event dict from SQLite
2. Endpoint handler converts → EventResponse Pydantic model
3. FastAPI serializes → JSON response
4. Client receives properly typed JSON

USAGE:
------
```python
from app.models import EventCreate, EventResponse, EventCategory

# In endpoint handler
@app.post("/api/events", response_model=EventResponse)
async def create_event(event: EventCreate, user_id: int):
    # event is automatically validated EventCreate instance
    # return value automatically serialized to EventResponse JSON
    pass
```

BENEFITS:
---------
- Type safety: Catch errors at request time, not in database
- Auto documentation: FastAPI generates OpenAPI docs from schemas
- IDE support: Autocomplete and type hints in editors
- Validation: Automatic checks for required fields, data types, ranges
- Serialization: Automatic JSON conversion with proper formatting

DEPENDENCIES:
-------------
- pydantic: BaseModel, Field for schema definition
- datetime: Timestamp fields
- enum: Category/Type/Urgency enums
- typing: Type hints (Optional, Dict, Any)

USED BY:
--------
- simple_main.py: All API endpoint request/response validation
- agents/data_collector.py: Parse output validation
- simple_jarvis_db.py: Type hints for database methods
"""
from .event import Event, EventCreate, EventResponse, EventCategory
from .pattern import Pattern, PatternResponse
from .intervention import Intervention, InterventionCreate, InterventionResponse, InterventionFeedback, InterventionType, InterventionUrgency

__all__ = ['Event', 'EventCreate', 'EventResponse', 'EventCategory', 'Pattern', 'PatternResponse', 'Intervention', 'InterventionCreate', 'InterventionResponse', 'InterventionFeedback', 'InterventionType', 'InterventionUrgency']