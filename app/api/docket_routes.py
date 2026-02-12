"""
Docket and district selection endpoints.
"""

import sys
import asyncio
from pathlib import Path

from fastapi import HTTPException, status

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.automation.docket_selection import DocketSelector
from src.utils.logger import get_logger
from src.utils.smart_waits import SmartWaits
from src.utils.popup_blocker import PopupBlocker
from api.app import app, browser_sessions, session_locks
from models.schemas import (
    DocketSelectionRequest,
    DocketSelectionResponse,
    DistrictSelectionRequest,
    DistrictSelectionResponse,
    DocketSearchRequest,
    DocketSearchResponse,
)

logger = get_logger(__name__)


@app.post("/api/v1/docket/select", response_model=DocketSelectionResponse)
async def select_docket(request: DocketSelectionRequest):
    """
    Select a docket category and specific docket.

    This handles: Content Types → Dockets → Category → Specific Docket
    """
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Get session lock to prevent concurrent operations on same session
    session_lock = session_locks.get(request.session_id)
    if not session_lock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session lock not found"
        )

    # Acquire session lock (blocking operation moved to thread)
    def _select_docket_with_lock():
        with session_lock:
            session = browser_sessions[request.session_id]
            driver = session["driver"]

            logger.info(f"Selecting docket for session {request.session_id}")
            logger.info(f"Category: {request.category}, Docket: {request.specific_docket}")

            docket_selector = DocketSelector()
            success = docket_selector.select_docket(
                driver,
                category=request.category,
                specific_docket=request.specific_docket
            )

            if success:
                session["state"] = "docket_selected"
                return True
            return False

    try:
        success = await asyncio.to_thread(_select_docket_with_lock)

        if success:
            return DocketSelectionResponse(
                status="success",
                message=f"Successfully selected {request.category} → {request.specific_docket}"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Docket selection failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Docket selection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docket selection failed: {str(e)}"
        )


@app.post("/api/v1/district/select", response_model=DistrictSelectionResponse)
async def select_district(request: DistrictSelectionRequest):
    """Select a district for the chosen state."""
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Get session lock to prevent concurrent operations on same session
    session_lock = session_locks.get(request.session_id)
    if not session_lock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session lock not found"
        )

    def _select_district_with_lock():
        with session_lock:
            session = browser_sessions[request.session_id]
            driver = session["driver"]

            logger.info(f"Selecting district for session {request.session_id}")
            logger.info(f"State: {request.state}, District: {request.district}")

            # Import here to avoid circular imports
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time

            # OPTIMIZED: Reduced timeout from 5s to 3s
            wait = WebDriverWait(driver, 3)

            # PHASE 1 OPTIMIZATION: Remove overlays proactively at start
            logger.info("Removing blocking overlays proactively...")
            PopupBlocker.remove_blocking_overlays(driver)

            # Map district names to their exact href paths
            district_href_map = {
                "Central District": "CaliforniaFederalDistrictCourtDocketsCentralDistrict",
                "Eastern District": "CaliforniaFederalDistrictCourtDocketsEasternDistrict",
                "Northern District": "CaliforniaFederalDistrictCourtDocketsNorthernDistrict",
                "Southern District": "CaliforniaFederalDistrictCourtDocketsSouthernDistrict"
            }

            district_href = district_href_map.get(request.district, "")

            district_selectors = []
            if district_href:
                district_selectors.extend([
                    (By.XPATH, f'//a[contains(@href, "{district_href}")]'),
                    (By.CSS_SELECTOR, f'a[href*="{district_href}"]'),
                ])

            district_selectors.extend([
                (By.XPATH, f'//a[text()="{request.district}"]'),
                (By.XPATH, f'//a[contains(text(), "{request.district}")]'),
            ])

            district_element = None
            for by_type, selector in district_selectors:
                try:
                    district_element = wait.until(
                        EC.element_to_be_clickable((by_type, selector))
                    )
                    logger.info(f"Found district with: {by_type}={selector}")
                    break
                except:
                    continue

            if not district_element:
                raise Exception(f"Cannot find district: {request.district}")

            # PHASE 3 OPTIMIZATION: Use instant scroll instead of smooth animation
            driver.execute_script("arguments[0].scrollIntoView(true);", district_element)
            # OPTIMIZED: Wait for element to be stable
            SmartWaits.wait_for_element_stable(driver, district_element, timeout=2)
            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            driver.execute_script("arguments[0].click();", district_element)
            logger.info(f"Clicked district: {request.district}")
            # OPTIMIZED: Wait for page load using smart wait (reduced from 3s to 2s)
            SmartWaits.wait_for_page_ready(driver, timeout=2)

            session["state"] = "district_selected"
            return True

    try:
        await asyncio.to_thread(_select_district_with_lock)

        return DistrictSelectionResponse(
            status="success",
            message=f"Successfully selected district: {request.district}"
        )

    except Exception as e:
        logger.error(f"District selection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"District selection failed: {str(e)}"
        )


@app.post("/api/v1/docket/search", response_model=DocketSearchResponse)
async def search_docket(request: DocketSearchRequest):
    """Search for a specific docket number."""
    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    # Get session lock to prevent concurrent operations on same session
    session_lock = session_locks.get(request.session_id)
    if not session_lock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session lock not found"
        )

    def _search_docket_with_lock():
        with session_lock:
            session = browser_sessions[request.session_id]
            driver = session["driver"]

            logger.info(f"Searching docket for session {request.session_id}")
            logger.info(f"Docket Number: {request.docket_number}")

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time

            # OPTIMIZED: Reduced timeout from 3s to 2s
            wait = WebDriverWait(driver, 2)

            # PHASE 1 OPTIMIZATION: Remove overlays proactively at start
            logger.info("Removing blocking overlays proactively...")
            PopupBlocker.remove_blocking_overlays(driver)

            # Find docket number input field
            input_selectors = [
                (By.ID, "co_search_advancedSearch_DN"),
                (By.NAME, "co_search_advancedSearch_DN"),
            ]

            input_element = None
            for by, selector in input_selectors:
                try:
                    input_element = wait.until(
                        EC.presence_of_element_located((by, selector))
                    )
                    break
                except:
                    continue

            if not input_element:
                raise Exception("Cannot find docket number input field")

            # Enter docket number
            input_element.clear()
            # OPTIMIZED: Reduced from 0.3s to 0.15s
            time.sleep(0.15)
            input_element.send_keys(request.docket_number)
            # OPTIMIZED: Reduced from 0.5s to 0.2s
            time.sleep(0.2)

            # Find and click search button
            search_selectors = [
                (By.ID, "searchButton"),
                (By.XPATH, '//button[@id="searchButton"]'),
            ]

            search_button = None
            for by, selector in search_selectors:
                try:
                    search_button = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    break
                except:
                    continue

            if not search_button:
                raise Exception("Cannot find search button")

            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            search_button.click()
            # OPTIMIZED: Wait for search results using smart wait (reduced from 3s to 2s)
            SmartWaits.wait_for_page_ready(driver, timeout=2)

            session["state"] = "docket_searched"
            return True

    try:
        await asyncio.to_thread(_search_docket_with_lock)

        return DocketSearchResponse(
            status="success",
            message=f"Successfully searched for docket: {request.docket_number}"
        )

    except Exception as e:
        logger.error(f"Docket search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Docket search failed: {str(e)}"
        )
