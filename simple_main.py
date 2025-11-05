"""
=============================================================================
JARVIS 3.0 - MAIN API SERVER (FastAPI Application Entry Point)
=============================================================================

PURPOSE:
--------
This is the CORE FastAPI application that serves as the main HTTP server for
JARVIS. It handles all incoming API requests, authentication, and routes them
to the appropriate handlers.

RESPONSIBILITY:
---------------
- Define all API endpoints (routes) for the application
- Handle HTTP requests/responses with proper status codes
- Integrate authentication (JWT tokens via simple_auth.py)
- Coordinate between database (simple_jarvis_db.py) and agents (DataCollectorAgent)
- Manage CORS for frontend access
- Provide health checks and error handling

DATA FLOW (Request → Response):
--------------------------------
1. CLIENT REQUEST arrives (HTTP POST/GET/DELETE with JSON/FormData)
   Example: POST /api/events/parse with body {"text": "ran 5k today"}

2. MIDDLEWARE checks CORS, handles preflight requests

3. AUTHENTICATION (if endpoint requires it):
   - Extract "Authorization: Bearer <token>" header
   - Call get_current_user() from simple_auth.py
   - Validates JWT token, returns user_id or raises 401 Unauthorized

4. ENDPOINT HANDLER receives request:
   - Validates request body against Pydantic schemas (EventCreate, etc.)
   - For natural language: calls DataCollectorAgent.parse() → LLM → structured JSON
   - For direct events: validates data and passes to database
   - For voice: transcribes with Whisper API → DataCollectorAgent.parse()

5. DATABASE OPERATIONS:
   - Call jarvis_db methods (create_event, get_events, etc.)
   - SQLite operations in simple_jarvis_db.py
   - Returns data or raises errors

6. RESPONSE FORMATTING:
   - Convert database results to Pydantic response models (EventResponse, etc.)
   - Add metadata (count, timestamp, etc.)
   - Return JSON with appropriate HTTP status code (200, 201, 404, 500)

7. CLIENT RECEIVES response JSON

DEPENDENCIES:
-------------
- simple_auth.py: JWT authentication, get_current_user()
- simple_jarvis_db.py: Database operations (jarvis_db singleton)
- agents/data_collector.py: Natural language parsing (DataCollectorAgent)
- app/models/event.py: Pydantic schemas for validation

KEY ENDPOINTS:
--------------
- POST   /api/events          → Manual event logging (direct JSON)
- POST   /api/events/parse    → Natural language parsing (text → structured event)
- POST   /api/events/voice    → Voice input (audio → text → event)
- POST   /api/events/quick    → Quick-tap mobile (instant, no LLM)
- GET    /api/events          → List events with filters (date, category, type)
- GET    /api/events/today    → Today's dashboard (grouped by dimension)
- DELETE /api/events/{id}     → Delete user's event (ownership check)
- GET    /api/stats           → User statistics
- GET    /health              → Health check (service status)
"""

import time
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio

# Import simple components
from simple_auth import router as auth_router, get_current_user
from simple_jarvis_db import jarvis_db
from app.models.event import EventCreate, EventResponse, EventCategory
from agents.data_collector import data_collector
from agents.pattern_detector import pattern_detector
from agents.forecaster import forecaster

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for events
class EventCreateRequest(BaseModel):
    category: EventCategory
    event_type: str
    feeling: Optional[str] = None
    data: Dict[str, Any] = {}


class EventListResponse(BaseModel):
    events: list
    count: int

class TodayStatusResponse(BaseModel):
    physical: Optional[Dict[str, Any]] = None
    mental: Dict[str, Any] = {"completed": 0, "total": 0}
    spiritual: Optional[Dict[str, Any]] = None
    mood: Optional[str] = None
    total_events: int = 0

class SuccessResponse(BaseModel):
    message: str
    data: Dict[str, Any] = {}

class HealthCheckResponse(BaseModel):
    status: str
    message: str
    version: str
    services: Dict[str, Any] = {}
    uptime_seconds: Optional[float] = None

# Create FastAPI application
app = FastAPI(
    title="JARVIS Backend",
    description="AI Assistant Backend with LLM Integration",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "timestamp": time.time()
        }
    )

# Root endpoints
@app.get("/", response_model=SuccessResponse)
async def root():
    """Root endpoint with API information"""
    return SuccessResponse(
        message="JARVIS 3.0 Backend - AI Assistant",
        data={
            "version": "3.0.0",
            "status": "operational",
            "docs": "/docs",
            "health": "/health",
            "endpoints": {
                "register": "/api/v1/auth/register",
                "login": "/api/v1/auth/login",
                "query": "/query (requires JWT)",
                "public_query": "/query/public (optional JWT)"
            }
        }
    )

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        stats = jarvis_db.get_stats(user_id=1) if jarvis_db else {}
        
        return HealthCheckResponse(
            status="healthy",
            message="JARVIS Backend is operational",
            version="3.0.0",
            services={
                "database": {"status": "healthy", "type": "SQLite"},
                "authentication": {"status": "healthy", "type": "JWT"},
                "event_tracking": {"status": "healthy", "total_events": stats.get("total_events", 0)},
                "api": {"status": "healthy", "endpoints": 8}
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            message=f"Health check failed: {str(e)}",
            version="3.0.0"
        )

# ==================== EVENT ENDPOINTS ====================

@app.post("/api/events", status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Log a new event (workout, task, meditation)
    Requires authentication
    """
    try:
        event_id = jarvis_db.create_event(
            user_id=current_user["id"],
            category=event_data.category.value,
            event_type=event_data.event_type,
            feeling=event_data.feeling,
            data=event_data.data
        )
        
        event = jarvis_db.get_event_by_id(event_id)
        
        return {
            "message": "Event logged successfully",
            "event": event
        }
        
    except Exception as e:
        logger.error(f"Failed to create event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log event: {str(e)}"
        )

@app.get("/api/events", response_model=EventListResponse)
async def get_events(
    category: Optional[str] = None,
    event_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Retrieve events with optional filters
    Requires authentication
    """
    try:
        events = jarvis_db.get_events(
            user_id=current_user["id"],
            category=category,
            event_type=event_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        
        return EventListResponse(
            events=events,
            count=len(events)
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve events: {str(e)}"
        )

@app.get("/api/events/today", response_model=TodayStatusResponse)
async def get_today_status(current_user: dict = Depends(get_current_user)):
    """
    Get today's status - all events logged today
    Requires authentication
    """
    try:
        events = jarvis_db.get_events_today(user_id=current_user["id"])
        
        # Organize by dimension
        status = {
            'physical': None,
            'mental': {'completed': 0, 'total': 0},
            'spiritual': None,
            'mood': None,
            'total_events': len(events)
        }
        
        for event in events:
            if event['category'] == 'physical':
                status['physical'] = {
                    'logged': True,
                    'event_type': event['event_type'],
                    'feeling': event.get('feeling'),
                    'data': event['data']
                }
                if event.get('feeling'):
                    status['mood'] = event['feeling']
                    
            elif event['category'] == 'mental':
                status['mental']['total'] += 1
                if event['data'].get('completed'):
                    status['mental']['completed'] += 1
                    
            elif event['category'] == 'spiritual':
                status['spiritual'] = {
                    'logged': True,
                    'event_type': event['event_type'],
                    'data': event['data']
                }
        
        return TodayStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Failed to get today's status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get today's status: {str(e)}"
        )

@app.delete("/api/events/{event_id}")
async def delete_event(
    event_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete an event
    Requires authentication
    """
    try:
        deleted = jarvis_db.delete_event(event_id, current_user["id"])
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found or you don't have permission to delete it"
            )
        
        return {"message": "Event deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete event: {str(e)}"
        )

# ==================== DATA COLLECTOR AGENT ENDPOINTS (DAY 2) ====================

@app.post("/api/events/parse", status_code=status.HTTP_201_CREATED)
async def parse_and_create_event(
    text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Parse natural language input and create event
    Examples: "upper body heavy felt great", "finished client proposal", "meditated 10 minutes"
    Requires authentication
    """
    try:
        # Parse using Data Collector Agent
        parsed = await data_collector.parse(text)
        
        # Check for parsing error
        if "error" in parsed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not parse input: {parsed['error']}"
            )
        
        # Create event from parsed data
        event_id = jarvis_db.create_event(
            user_id=current_user["id"],
            category=parsed['dimension'],
            event_type=parsed['type'],
            feeling=parsed.get('feeling'),
            data=parsed['data']
        )
        
        event = jarvis_db.get_event_by_id(event_id)
        
        return {
            "message": "Event parsed and logged successfully",
            "event": event,
            "parsed_from": text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse and create event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse event: {str(e)}"
        )

@app.post("/api/events/voice", status_code=status.HTTP_201_CREATED)
async def voice_input(
    audio: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Voice input endpoint - transcribe audio and parse into event
    Accepts audio file (mp3, wav, m4a, etc.)
    Requires authentication
    
    NOTE: Requires OpenAI API key for Whisper transcription
    Cost: ~$0.006 per minute of audio
    """
    try:
        # Check if OpenAI API key is available
        import os
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Voice input requires OpenAI API key (Whisper API not configured)"
            )
        
        # Read audio file
        audio_bytes = await audio.read()
        
        # Transcribe using OpenAI Whisper API
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Save temp file for Whisper API
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio_path = temp_audio.name
        
        try:
            with open(temp_audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            text = transcription.text
        finally:
            # Clean up temp file
            import os
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
        
        logger.info(f"Transcribed audio: {text}")
        
        # Parse the transcribed text
        parsed = await data_collector.parse(text)
        
        if "error" in parsed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not parse transcription: {parsed['error']}"
            )
        
        # Create event
        event_id = jarvis_db.create_event(
            user_id=current_user["id"],
            category=parsed['dimension'],
            event_type=parsed['type'],
            feeling=parsed.get('feeling'),
            data=parsed['data']
        )
        
        event = jarvis_db.get_event_by_id(event_id)
        
        return {
            "message": "Voice input processed successfully",
            "transcription": text,
            "event": event
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process voice input: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice input: {str(e)}"
        )

@app.post("/api/events/quick", status_code=status.HTTP_201_CREATED)
async def quick_tap_event(
    event_data: EventCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Quick tap event logging (no LLM parsing needed)
    For mobile quick-tap UI with pre-selected options
    Instant response, no AI processing cost
    Requires authentication
    """
    try:
        event_id = jarvis_db.create_event(
            user_id=current_user["id"],
            category=event_data.category.value,
            event_type=event_data.event_type,
            feeling=event_data.feeling,
            data=event_data.data
        )
        
        event = jarvis_db.get_event_by_id(event_id)
        
        return {
            "message": "Event logged instantly",
            "event": event,
            "processing_method": "quick_tap"
        }
        
    except Exception as e:
        logger.error(f"Failed to create quick event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log event: {str(e)}"
        )

@app.get("/api/stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """
    Get user statistics
    Requires authentication
    """
    try:
        stats = jarvis_db.get_stats(user_id=current_user["id"])
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@app.post("/api/insights/generate")
async def generate_insights(
    days: int = 90,
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger pattern detection for the authenticated user and return detected patterns.
    Optional: specify number of days to analyze (default 90).
    Requires authentication.
    """
    try:
        # Run the detector (async)
        patterns = await pattern_detector.detect_patterns(current_user["id"], limit=days)

        return {
            "message": "Insights generated",
            "patterns": patterns,
            "count": len(patterns)
        }

    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@app.post("/api/forecast")
async def generate_forecast(days: int = 7, current_user: dict = Depends(get_current_user)):
    """Trigger forecaster to generate a short-term forecast for the user (default 7 days)."""
    try:
        result = await forecaster.generate_forecast(current_user["id"], days)
        return {"message": "Forecast generated", "forecast": result}
    except Exception as e:
        logger.error(f"Failed to generate forecast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forecast: {str(e)}"
        )

# ==================== OLD ENDPOINTS (TO BE REMOVED) ====================

@app.post("/query")
async def process_query_deprecated(current_user: dict = Depends(get_current_user)):
    """DEPRECATED: Use /api/events instead"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint has been deprecated. Use /api/events instead"
    )

@app.post("/query/public")
async def process_public_query_deprecated():
    """DEPRECATED: Use /api/events instead"""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint has been deprecated. Use /api/events instead"
    )

@app.get("/system/status")
async def system_status(current_user: dict = Depends(get_current_user)):
    """Get detailed system status (requires auth)"""
    try:
        stats = jarvis_db.get_stats(user_id=current_user["id"])
        
        return SuccessResponse(
            message="System status retrieved successfully",
            data={
                "user": {
                    "id": current_user["id"],
                    "email": current_user["email"]
                },
                "stats": stats
            }
        )
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System status check failed: {str(e)}"
        )

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "ok", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    
    print("Starting JARVIS Backend...")
    print("Available endpoints:")
    print("- POST /api/v1/auth/register - Register new user")
    print("- POST /api/v1/auth/login - Login and get JWT")
    print("")
    print("Event Logging:")
    print("- POST /api/events - Log event (structured data)")
    print("- POST /api/events/parse - Parse natural language input")
    print("- POST /api/events/voice - Voice input (audio file)")
    print("- POST /api/events/quick - Quick tap (instant, no AI)")
    print("- GET /api/events - Retrieve events with filters")
    print("- GET /api/events/today - Today's status dashboard")
    print("- DELETE /api/events/{id} - Delete event")
    print("")
    print("Statistics & Health:")
    print("- GET /api/stats - User statistics")
    print("- GET /health - Health check")
    print("- GET /docs - API documentation")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )