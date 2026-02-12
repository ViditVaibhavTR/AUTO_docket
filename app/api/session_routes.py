"""
Session management and automation initialization endpoints.
"""

import sys
import uuid
import asyncio
import time
from pathlib import Path
from threading import Lock
from datetime import datetime

from fastapi import HTTPException, status, Request

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.automation.browser import BrowserManager
from src.automation.gateway_config import GatewayConfigurator
from src.automation.iac_config import IACConfigurator
from src.automation.westlaw_login import WestLawLogin
from src.utils.logger import get_logger
from api.app import app, browser_sessions, sessions_lock, session_locks, session_timeouts
from models.schemas import (
    AutomationStartRequest,
    AutomationStartResponse,
    SessionCleanupRequest,
    SessionCleanupResponse,
)

logger = get_logger(__name__)

# Rate limiting configuration
active_automations = {}  # {client_ip: timestamp}
MAX_CONCURRENT_AUTOMATIONS = 2
RATE_LIMIT_SECONDS = 30


@app.post("/api/v1/automation/start", response_model=AutomationStartResponse)
async def start_automation(automation_request: AutomationStartRequest, request: Request):
    """
    Start the automation process: login and configure gateway/IAC.

    Returns a session ID for subsequent requests.
    """
    # Rate limiting check
    current_time = time.time()

    # Check concurrent automation limit
    if len(browser_sessions) >= MAX_CONCURRENT_AUTOMATIONS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many concurrent sessions. Maximum {MAX_CONCURRENT_AUTOMATIONS} allowed. "
                   f"Current: {len(browser_sessions)}. Please cleanup unused sessions."
        )

    # Clean up old "in progress" markers (older than 5 minutes)
    stale_markers = [
        ip for ip, ts in active_automations.items()
        if current_time - ts > 300
    ]
    for ip in stale_markers:
        del active_automations[ip]

    # Get client IP (for rate limiting)
    client_ip = request.client.host if request.client else 'unknown'

    # Check if automation already in progress for this IP
    if client_ip in active_automations:
        time_since = current_time - active_automations[client_ip]
        if time_since < RATE_LIMIT_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Automation already in progress for your session. "
                       f"Please wait {int(RATE_LIMIT_SECONDS - time_since)} seconds."
            )

    # Mark automation as in progress
    active_automations[client_ip] = current_time

    browser_manager = None
    session_id = str(uuid.uuid4())

    try:
        logger.info(f"Starting automation for session {session_id} from {client_ip}")

        # Validate configuration (sync operation, quick)
        settings.validate()

        # Run blocking browser operations in thread pool
        def _start_browser_automation():
            nonlocal browser_manager
            # Start browser
            browser_manager = BrowserManager()
            driver = browser_manager.start()

            # Navigate to routing page
            browser_manager.login()

            # Configure Gateway Live External (allow failures)
            try:
                gateway_config = GatewayConfigurator()
                gateway_config.configure_gateway(driver)
            except Exception as e:
                logger.warning(f"Gateway configuration failed (continuing): {e}")

            # Configure Infrastructure Access Controls
            iac_config = IACConfigurator()
            iac_config.configure_iac(driver)

            # Login to WestLaw Precision
            westlaw_login = WestLawLogin()
            westlaw_login.login(driver)

            return driver, browser_manager

        # Run blocking operations in separate thread
        driver, browser_manager = await asyncio.to_thread(_start_browser_automation)

        # Store session with lock
        with sessions_lock:
            browser_sessions[session_id] = {
                "driver": driver,
                "browser_manager": browser_manager,
                "state": "logged_in"
            }
            session_locks[session_id] = Lock()
            session_timeouts[session_id] = datetime.now()

        logger.info(f"Automation started successfully for session {session_id}")

        # Remove "in progress" marker on success
        if client_ip in active_automations:
            del active_automations[client_ip]

        return AutomationStartResponse(
            status="login_success",
            message="Successfully logged in and configured",
            session_id=session_id
        )

    except Exception as e:
        logger.error(f"Automation failed for session {session_id}: {e}")

        # Remove "in progress" marker on error
        if client_ip in active_automations:
            del active_automations[client_ip]

        if browser_manager:
            await asyncio.to_thread(browser_manager.cleanup)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Automation failed: {str(e)}"
        )


@app.post("/api/v1/session/cleanup", response_model=SessionCleanupResponse)
async def cleanup_session(request: SessionCleanupRequest):
    """Cleanup a browser session."""
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    try:
        session = browser_sessions[request.session_id]
        browser_manager = session.get("browser_manager")

        if browser_manager:
            await asyncio.to_thread(browser_manager.cleanup)

        with sessions_lock:
            if request.session_id in browser_sessions:
                del browser_sessions[request.session_id]
            if request.session_id in session_locks:
                del session_locks[request.session_id]
            if request.session_id in session_timeouts:
                del session_timeouts[request.session_id]

        return SessionCleanupResponse(
            status="success",
            message=f"Session {request.session_id} cleaned up successfully"
        )

    except Exception as e:
        logger.error(f"Session cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session cleanup failed: {str(e)}"
        )


@app.get("/api/v1/sessions")
async def list_sessions():
    """List all active browser sessions."""
    return {
        "active_sessions": list(browser_sessions.keys()),
        "count": len(browser_sessions)
    }
