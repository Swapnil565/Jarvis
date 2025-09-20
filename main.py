import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
class DatabaseConnection:
    def __init__(self):
        self.connection = None
    
    def connect(self):
        try:
            database_url = os.getenv("DATABASE_URL", "postgresql://context_user:dev_password@localhost:5432/context_dev")
            self.connection = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def close(self):
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

# Global database instance
db = DatabaseConnection()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting JARVIS Backend...")
    db.connect()
    yield
    # Shutdown
    logger.info("Shutting down JARVIS Backend...")
    db.close()

# Create FastAPI app
app = FastAPI(
    title="JARVIS 3.0 Backend",
    description="AI Assistant Backend with Advanced Capabilities",
    version="0.1.0",
    lifespan=lifespan
)

# Response models
class HealthResponse(BaseModel):
    status: str
    message: str
    database: str
    redis: str = "not_configured"

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "JARVIS 3.0 Backend is running!",
        "version": "0.1.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint that verifies database connectivity"""
    try:
        # Check database connectivity
        db_status = "connected"
        if db.connection:
            cursor = db.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            if not result:
                db_status = "error"
        else:
            db_status = "disconnected"
            
        return HealthResponse(
            status="healthy" if db_status == "connected" else "unhealthy",
            message="JARVIS Backend is operational" if db_status == "connected" else "Database connection issues",
            database=db_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

