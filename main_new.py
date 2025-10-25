"""
JARVIS 3.0 Backend - Application Launcher

This file serves as the entry point for the JARVIS 3.0 backend application.
It imports and runs the FastAPI app from the new modular structure.
"""

import uvicorn
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True
    )