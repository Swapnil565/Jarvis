"""
JARVIS 3.0 - Simplified Main Application
Single file FastAPI app with all required functionality for Day 2 checklist
"""

import time
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio

# Import simple components
from simple_auth import router as auth_router, get_current_user
from jarvis_router import process_jarvis_query

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

class QueryResponse(BaseModel):
    response: str
    status: str
    query_analysis: Dict[str, Any] = {}
    processing_time_ms: float

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
    title="JARVIS 3.0 Backend",
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
        from jarvis_router import router
        llm_status = router.get_status()
        
        return HealthCheckResponse(
            status="healthy",
            message="JARVIS Backend is operational",
            version="3.0.0",
            services={
                "database": {"status": "healthy", "type": "SQLite"},
                "authentication": {"status": "healthy", "type": "JWT"},
                "llm_router": {"status": "healthy", "providers": len(llm_status.get("rate_limits", {}))},
                "api": {"status": "healthy", "endpoints": 5}
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            message=f"Health check failed: {str(e)}",
            version="3.0.0"
        )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process a user query through JARVIS AI system
    Requires authentication
    """
    start_time = time.time()
    
    try:
        # Add user context to the request
        user_context = {
            "user_id": current_user["id"],
            "user_email": current_user["email"],
            "authenticated": True,
            **request.context
        }
        
        # Process the query through JARVIS LLM router
        result = await process_jarvis_query(request.query, user_context)
        
        processing_time = (time.time() - start_time) * 1000
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Query processing failed")
            )
        
        return QueryResponse(
            response=result["response"],
            status="success" if result["success"] else "error",
            query_analysis={
                "model_used": result.get("model_used", "unknown"),
                "task_type": result.get("task_type", "unknown"),
                "processing_time": result.get("processing_time", 0)
            },
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )

@app.post("/query/public", response_model=QueryResponse)
async def process_public_query(request: QueryRequest):
    """
    Process a public query through JARVIS AI system
    Authentication optional - limited functionality
    """
    start_time = time.time()
    
    try:
        # Anonymous user context
        user_context = {
            "user_id": None,
            "authenticated": False,
            "rate_limited": True,
            **request.context
        }
        
        # Process the query through JARVIS LLM router
        result = await process_jarvis_query(request.query, user_context)
        
        processing_time = (time.time() - start_time) * 1000
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Query processing failed")
            )
        
        return QueryResponse(
            response=result["response"],
            status="success" if result["success"] else "error",
            query_analysis={
                "model_used": result.get("model_used", "unknown"),
                "task_type": result.get("task_type", "unknown"),
                "processing_time": result.get("processing_time", 0)
            },
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Public query processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query processing failed: {str(e)}"
        )

@app.get("/system/status")
async def system_status():
    """Get detailed system status"""
    try:
        from jarvis_router import router
        status_data = router.get_status()
        
        return SuccessResponse(
            message="System status retrieved successfully",
            data=status_data
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
    
    print("Starting JARVIS 3.0 Backend...")
    print("Available endpoints:")
    print("- POST /api/v1/auth/register - Register new user")
    print("- POST /api/v1/auth/login - Login and get JWT")
    print("- POST /query - AI chat (requires JWT)")
    print("- POST /query/public - Public AI chat")
    print("- GET /health - Health check")
    print("- GET /docs - API documentation")
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )