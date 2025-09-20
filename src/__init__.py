"""
JARVIS 3.0 Backend - Core Application Module

This module contains the main application entry point and core system components
for the Context Resurrection AI Assistant.
"""

from .main import app
from .core.context_resurrection import ContextResurrectionCore

__version__ = "0.1.0"
__author__ = "JARVIS Team"
__description__ = "AI Assistant Backend with Advanced Context Capabilities"

__all__ = ["app", "ContextResurrectionCore"]