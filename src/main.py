"""
JARVIS 3.0 - Main Application Entry Point

This module contains the FastAPI application with all endpoints,
middleware, and core system integration.
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

from .core.context_resurrection import ContextResurrectionCore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
jarvis_core: ContextResurrectionCore = None
db_connection = None

# Database connection management
class DatabaseConnection:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        try:
            database_url = os.getenv("DATABASE_URL", "postgresql://context_user:dev_password@localhost:5432/context_dev")
            self.connection = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params=None):
        """Execute a database query"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global jarvis_core, db_connection
    
    # Startup
    logger.info("🚀 Starting JARVIS 3.0 Backend...")
    
    # Initialize core system
    jarvis_core = ContextResurrectionCore()
    
    # Initialize database
    db_connection = DatabaseConnection()
    db_connection.connect()
    
    logger.info("✅ JARVIS 3.0 Backend startup complete")
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down JARVIS 3.0 Backend...")
    if db_connection:
        db_connection.close()
    logger.info("✅ JARVIS 3.0 Backend shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="JARVIS 3.0 Backend",
    description="AI Assistant Backend with Advanced Context Resurrection Capabilities",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response models
class HealthResponse(BaseModel):
    status: str
    message: str
    database: str
    core_system: Dict[str, Any]
    timestamp: float
    version: str

class QueryRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

class QueryResponse(BaseModel):
    response: str
    status: str
    query_analysis: Dict[str, Any] = {}
    processing_time_ms: float

# Dependency to get database connection
def get_db():
    if not db_connection or not db_connection.connection:
        raise HTTPException(status_code=503, detail="Database not available")
    return db_connection

# Dependency to get JARVIS core
def get_jarvis_core():
    if not jarvis_core:
        raise HTTPException(status_code=503, detail="JARVIS core not initialized")
    return jarvis_core

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🤖 JARVIS 3.0 Backend - Context Resurrection AI",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "Context Resurrection",
            "Vector Search",
            "Personal Memory",
            "Query Intelligence",
            "Multi-modal Processing"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check(
    db: DatabaseConnection = Depends(get_db),
    core: ContextResurrectionCore = Depends(get_jarvis_core)
):
    """Comprehensive health check endpoint"""
    start_time = time.time()
    
    try:
        # Check database connectivity
        db_status = "connected"
        if db.connection:
            result = db.execute_query("SELECT 1 as test")
            if not result or result[0]['test'] != 1:
                db_status = "error"
        else:
            db_status = "disconnected"
        
        # Get core system status
        core_status = await core.health_status()
        
        # Check if system is healthy
        is_healthy = (
            db_status == "connected" and 
            core_status["status"] == "healthy"
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            message=f"JARVIS Backend is {'operational' if is_healthy else 'experiencing issues'}",
            database=db_status,
            core_system=core_status,
            timestamp=time.time(),
            version="0.1.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Service unavailable: {str(e)}"
        )

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    core: ContextResurrectionCore = Depends(get_jarvis_core)
):
    """Process a user query through JARVIS AI system"""
    start_time = time.time()
    
    try:
        # Process the query through JARVIS core
        result = await core.process_request(request.query, request.context)
        
        processing_time = (time.time() - start_time) * 1000
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Query processing failed")
            )
        
        return QueryResponse(
            response=result["response"],
            status=result["status"],
            query_analysis=result.get("query_analysis", {}),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/system/status")
async def system_status(core: ContextResurrectionCore = Depends(get_jarvis_core)):
    """Get detailed system status"""
    return await core.health_status()

@app.get("/demo")
async def demo_endpoint():
    """Demo endpoint showcasing JARVIS capabilities"""
    return {
        "message": "🚀 JARVIS 3.0 Context Resurrection Demo",
        "capabilities": {
            "data_ingestion": "Multi-source data processing",
            "vector_search": "Semantic similarity search",
            "personal_memory": "Context-aware memory system", 
            "query_intelligence": "Advanced query understanding",
            "response_generation": "Contextual response synthesis",
            "security": "Enterprise-grade authentication",
            "integrations": "External API orchestration"
        },
        "architecture": {
            "backend": "FastAPI + PostgreSQL + Redis",
            "ai_models": "OpenAI GPT + Custom embeddings",
            "vector_db": "pgvector for similarity search",
            "deployment": "Docker + Kubernetes ready"
        },
        "status": "All systems operational! 🎯"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )