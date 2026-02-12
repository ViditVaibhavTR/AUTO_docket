"""
FastAPI application initialization and configuration.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict
from threading import Lock
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global session storage (in production, use Redis or database)
browser_sessions: Dict[str, dict] = {}
# Lock for modifying browser_sessions dictionary
sessions_lock = Lock()
# Individual locks per session to prevent concurrent operations on same session
session_locks: Dict[str, Lock] = {}
# Session timeout tracking
session_timeouts: Dict[str, datetime] = {}
SESSION_TIMEOUT_MINUTES = 30


async def cleanup_stale_sessions():
    """Background task to cleanup stale sessions."""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute

            current_time = datetime.now()
            stale_sessions = []

            # Find sessions older than timeout
            for session_id, created_at in list(session_timeouts.items()):
                age = current_time - created_at
                if age > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                    stale_sessions.append(session_id)

            # Cleanup stale sessions
            for session_id in stale_sessions:
                logger.info(f"Cleaning up stale session: {session_id}")
                if session_id in browser_sessions:
                    session = browser_sessions[session_id]
                    if session.get("browser_manager"):
                        await asyncio.to_thread(session["browser_manager"].cleanup)

                    with sessions_lock:
                        del browser_sessions[session_id]
                        if session_id in session_locks:
                            del session_locks[session_id]
                        if session_id in session_timeouts:
                            del session_timeouts[session_id]

        except Exception as e:
            logger.error(f"Error in stale session cleanup: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app with automatic cleanup."""
    logger.info("Starting Docket Alert Automation API")

    # Start background cleanup task
    cleanup_task = asyncio.create_task(cleanup_stale_sessions())

    yield

    logger.info("Shutting down Docket Alert Automation API")

    # Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    # Cleanup all browser sessions
    for session_id in list(browser_sessions.keys()):
        try:
            session = browser_sessions[session_id]
            if session.get("browser_manager"):
                await asyncio.to_thread(session["browser_manager"].cleanup)
            with sessions_lock:
                if session_id in browser_sessions:
                    del browser_sessions[session_id]
                if session_id in session_locks:
                    del session_locks[session_id]
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="Docket Alert Automation API",
    description="REST API for automating docket alert creation on WestLaw Precision",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes to register them with the app
# These imports must come after app is created to avoid circular imports
from api import health_routes, session_routes, docket_routes, alert_routes  # noqa: E402, F401
