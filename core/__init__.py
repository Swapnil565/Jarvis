"""Core shim package for compatibility.
This package re-exports modules that were referenced as `core.*`.
"""

from . import simple_jarvis_db

__all__ = ["simple_jarvis_db"]
