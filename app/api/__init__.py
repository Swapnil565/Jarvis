"""
API package for JARVIS 3.0 Backend
Contains all API routes and endpoints
"""

from .v1 import api_router

__all__ = ["api_router"]