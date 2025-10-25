"""
API v1 router for JARVIS 3.0 Backend
Main API router that includes all v1 endpoints
"""

from fastapi import APIRouter

# Import all routers
from .auth import router as auth_router
from .users import router as users_router  
from .documents import router as documents_router
from .conversations import router as conversations_router
from .search import router as search_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])

# Health check for API
@api_router.get("/health")
async def api_health():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "documents": "/api/v1/documents", 
            "conversations": "/api/v1/conversations",
            "search": "/api/v1/search"
        }
    }