"""
JAimport time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional 3.0 - Main Application Entry Point

This module contains the FastAPI application with all endpoints,
middleware, and core system integration using the new modular structure.
"""

import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core import get_db, settings
from .schemas import (
    HealthCheckResponse, SuccessResponse, ErrorResponse,
    BaseResponse, QueryRequest, QueryResponse
)
from .utils.metrics import get_health_metrics, MetricsCollector
from .api.v1 import api_router
from .auth.auth_bearer import JWTBearer, get_current_user, OptionalJWTBearer
from .models.user import User

# Import the working LLM router
from .jarvis_router import process_jarvis_query

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
metrics_collector: MetricsCollector = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global metrics_collector
    
    # Startup
    logger.info("Starting JARVIS 3.0 Backend...")
    
    try:
        # Initialize database (optional for development)
        try:
            from .core.database import init_db
            await init_db()
            logger.info("Database initialized")
        except Exception as db_e:
            logger.warning(f"Database initialization failed (will work without DB): {db_e}")
        
        # Initialize metrics collector
        if hasattr(settings, 'enable_metrics') and settings.enable_metrics:
            metrics_collector = MetricsCollector()
            logger.info("Metrics collector initialized")
        
        logger.info("JARVIS 3.0 Backend startup complete")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        # Don't raise - allow app to start without full features
    
    yield
    
    # Shutdown
    logger.info("Shutting down JARVIS 3.0 Backend...")
    
    try:
        # Close database connections
        try:
            from .core.database import close_db
            await close_db()
            logger.info("Database connections closed")
        except:
            pass
        
        # Cleanup metrics collector
        if metrics_collector:
            await metrics_collector.cleanup()
            logger.info("Metrics collector cleaned up")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
    
    logger.info("JARVIS 3.0 Backend shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI Assistant Backend with Advanced Context Resurrection Capabilities",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": time.time()
        }
    )

# No dependency needed - using direct function call to jarvis_router

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Root endpoints
@app.get("/", response_model=SuccessResponse)
async def root():
    """Root endpoint with API information"""
    return SuccessResponse(
        message="🤖 JARVIS 3.0 Backend - Context Resurrection AI",
        data={
            "version": settings.version,
            "status": "operational",
            "environment": settings.environment,
            "docs": "/docs" if settings.debug else None,
            "health": "/health",
            "api": "/api/v1",
            "features": [
                "Context Resurrection",
                "Vector Search", 
                "Personal Memory",
                "Query Intelligence",
                "Multi-modal Processing",
                "Authentication & Security",
                "Real-time Chat",
                "Document Processing"
            ],
            "architecture": {
                "backend": "FastAPI + PostgreSQL + Redis",
                "ai_models": "OpenAI GPT + Custom embeddings",
                "vector_db": "pgvector for similarity search",
                "deployment": "Docker + Kubernetes ready"
            }
        }
    )

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Get comprehensive health metrics
        health_data = await get_health_metrics()
        
        # Determine overall health status
        all_healthy = all(
            service.get("status") == "healthy" 
            for service in health_data["services"].values()
        )
        
        return HealthCheckResponse(
            status="healthy" if all_healthy else "unhealthy",
            message=f"JARVIS Backend is {'operational' if all_healthy else 'experiencing issues'}",
            version=settings.version,
            services=health_data["services"],
            uptime_seconds=health_data.get("uptime_seconds")
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)  # 🔒 Protected endpoint
):
    """
    Process a user query through JARVIS AI system
    🔒 Requires authentication
    """
    start_time = time.time()
    
    try:
        # Add user context to the request
        user_context = {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "user_preferences": getattr(current_user, 'preferences', {}),
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
async def process_public_query(
    request: QueryRequest,
    current_user: Optional[User] = Depends(OptionalJWTBearer())  # 🔓 Optional auth
):
    """
    Process a public query through JARVIS AI system
    🔓 Authentication optional - limited functionality for non-authenticated users
    """
    start_time = time.time()
    
    try:
        # Add user context if authenticated, otherwise use anonymous context
        if current_user:
            user_context = {
                "user_id": current_user.id,
                "user_email": current_user.email,
                "authenticated": True,
                **request.context
            }
        else:
            user_context = {
                "user_id": None,
                "authenticated": False,
                "rate_limited": True,  # Apply rate limiting for anonymous users
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
        # Import router status
        from .jarvis_router import router
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

@app.get("/demo")
async def demo_endpoint():
    """Demo endpoint showcasing JARVIS capabilities"""
    return SuccessResponse(
        message="🚀 JARVIS 3.0 Context Resurrection Demo",
        data={
            "capabilities": {
                "data_ingestion": "Multi-source data processing",
                "vector_search": "Semantic similarity search",
                "personal_memory": "Context-aware memory system",
                "query_intelligence": "Advanced query understanding",
                "response_generation": "Contextual response synthesis",
                "security": "Enterprise-grade authentication",
                "integrations": "External API orchestration",
                "document_processing": "PDF, DOCX, TXT support",
                "real_time_chat": "WebSocket-based conversations"
            },
            "endpoints": {
                "authentication": "/api/v1/auth",
                "users": "/api/v1/users",
                "documents": "/api/v1/documents", 
                "conversations": "/api/v1/conversations",
                "search": "/api/v1/search"
            },
            "environment": settings.environment,
            "version": settings.version,
            "status": "All systems operational! 🎯"
        }
    )

# Health check for load balancers
@app.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers"""
    return {"status": "ok", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )