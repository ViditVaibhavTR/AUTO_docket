"""
Main entry point for the API - imports from the new modular structure.
This file exists for backward compatibility with existing commands.
"""

# Import the FastAPI app (routes are auto-registered in app.py)
from api.app import app  # noqa: F401

# Re-export app for uvicorn
__all__ = ["app"]
