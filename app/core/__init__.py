"""
Core module for JARVIS 3.0 Backend
Contains configuration, database, and AI system core
"""

from .config import settings, get_settings

__all__ = [
    "settings",
    "get_settings"
]