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
import threading
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



def _keep_chrome_hidden(session_id):
    """Background thread: continuously hide all Chrome windows every 0.5s."""
    import ctypes
    import ctypes.wintypes

    WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL,
        ctypes.wintypes.HWND,
        ctypes.wintypes.LPARAM
    )

    def _hide_callback(hwnd, _):
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            if 'Chrome' in buf.value or 'chrome' in buf.value:
                ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
        return True

    callback = WNDENUMPROC(_hide_callback)

    while session_id in browser_sessions:
        try:
            ctypes.windll.user32.EnumWindows(callback, 0)
        except Exception:
            pass
        time.sleep(0.5)


def _poll_for_login_complete(session_id, driver):
    """Background thread: poll browser every 2s until WestLaw home page detected.
    After detection: hide Chrome window via Windows API (same browser, session intact)."""
    max_wait = 300  # 5 minutes max
    start = time.time()
    while time.time() - start < max_wait:
        try:
            url = driver.current_url
            if 'next.westlaw.com' in url or 'next.qed.westlaw.com' in url:
                page = driver.page_source
                if 'Sign in' not in page and 'co_clientIDTextbox' not in page and ('History' in page or 'Folders' in page):
                    logger.info(f'WestLaw login complete for session {session_id}')

                    # Hide ALL Chrome windows using Windows API SW_HIDE
                    # SW_HIDE makes windows completely vanish (not even in taskbar)
                    try:
                        import ctypes
                        import ctypes.wintypes

                        def _hide_chrome_callback(hwnd, _):
                            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                            if length > 0:
                                buf = ctypes.create_unicode_buffer(length + 1)
                                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                                title = buf.value
                                if 'Chrome' in title or 'chrome' in title:
                                    ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE
                            return True

                        WNDENUMPROC = ctypes.WINFUNCTYPE(
                            ctypes.wintypes.BOOL,
                            ctypes.wintypes.HWND,
                            ctypes.wintypes.LPARAM
                        )
                        ctypes.windll.user32.EnumWindows(WNDENUMPROC(_hide_chrome_callback), 0)
                        logger.info('Chrome windows hidden via Windows API (SW_HIDE)')
                    except Exception as e:
                        logger.warning(f'Could not hide Chrome window: {e}')
                        try:
                            driver.minimize_window()
                        except Exception:
                            pass

                    # Move Chrome off-screen — new tabs inherit this position (no flash)
                    try:
                        driver.set_window_position(-32000, -32000)
                    except Exception:
                        pass

                    # Start persistent Chrome-hiding thread for new tabs
                    threading.Thread(
                        target=_keep_chrome_hidden,
                        args=(session_id,),
                        daemon=True
                    ).start()
                    logger.info('Started persistent Chrome window hider')

                    if session_id in browser_sessions:
                        browser_sessions[session_id]['state'] = 'logged_in'

                    logger.info(f'Login confirmed for session {session_id}')
                    return
        except Exception as e:
            logger.debug(f'Poll check error: {e}')
        time.sleep(2)
    logger.warning(f'Login detection timed out for session {session_id}')


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

            # Phase 1: Headless browser for gateway + IAC config (user doesn't see this)
            settings.HEADLESS = True
            browser_manager = BrowserManager()
            driver = browser_manager.start()

            browser_manager.login()

            try:
                gateway_config = GatewayConfigurator()
                gateway_config.configure_gateway(driver)
            except Exception as e:
                logger.warning(f"Gateway configuration failed (continuing): {e}")

            iac_config = IACConfigurator()
            iac_config.configure_iac(driver)

            logger.info("Gateway and IAC configured in headless mode")

            # Capture cookies and current URL from headless browser
            cookies = driver.get_cookies()
            login_url = driver.current_url
            driver.quit()
            logger.info("Closed headless browser after config")

            # Phase 2: Open visible browser directly on login page
            settings.HEADLESS = False
            browser_manager = BrowserManager()
            driver = browser_manager.start()

            # Navigate to login URL and inject cookies
            driver.get(login_url)
            time.sleep(1)
            driver.delete_all_cookies()
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass
            driver.get(login_url)
            time.sleep(1)

            logger.info("Visible browser opened on login page for user")

            return driver, browser_manager

        # Run blocking operations in separate thread
        driver, browser_manager = await asyncio.to_thread(_start_browser_automation)

        # Store session with lock
        with sessions_lock:
            browser_sessions[session_id] = {
                "driver": driver,
                "browser_manager": browser_manager,
                "state": "awaiting_login"
            }
            session_locks[session_id] = Lock()
            session_timeouts[session_id] = datetime.now()

        # Start background thread to detect when user completes login
        threading.Thread(
            target=_poll_for_login_complete,
            args=(session_id, driver),
            daemon=True
        ).start()

        logger.info(f"Automation started for session {session_id} - awaiting user login")

        # Remove "in progress" marker on success
        if client_ip in active_automations:
            del active_automations[client_ip]

        return AutomationStartResponse(
            status="awaiting_login",
            message="Gateway and IAC configured. Please login to WestLaw in the browser.",
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



@app.get("/api/v1/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current session state. Frontend polls this to detect login completion."""
    if session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"status": browser_sessions[session_id].get("state", "unknown")}


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
