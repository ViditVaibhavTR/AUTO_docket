"""
Docket and district selection endpoints.
"""

import sys
import asyncio
import time
from pathlib import Path

from fastapi import HTTPException, status

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.automation.docket_selection import DocketSelector
from src.utils.logger import get_logger
from src.utils.smart_waits import SmartWaits
from src.utils.popup_blocker import PopupBlocker
from src.utils.screenshot import ScreenshotManager
from api.app import app, browser_sessions, session_locks
from models.schemas import (
    DocketSelectionRequest,
    DocketSelectionResponse,
    DistrictSelectionRequest,
    DistrictSelectionResponse,
    DocketSearchRequest,
    DocketSearchResponse,
    MultiDocketRequest,
    MultiDocketResponse,
    MultiDocketResult,
)
from src.automation.tab_manager import TabManager

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

            # Map district names to state-agnostic href suffixes
            district_href_map = {
                "Central District": "CentralDistrict",
                "Eastern District": "EasternDistrict",
                "Northern District": "NorthernDistrict",
                "Southern District": "SouthernDistrict",
                "Western District": "WesternDistrict",
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
            logger.info("Waiting for search results page to load completely...")

            # Step 1: Wait for document to be ready (increased from 2s to 10s)
            SmartWaits.wait_for_page_ready(driver, timeout=10)
            logger.info("✓ Document ready")

            # Step 2: Wait for AJAX requests to complete
            SmartWaits.wait_for_ajax_complete(driver, timeout=5)
            logger.info("✓ AJAX requests complete")

            # Step 3: Scroll to top to ensure header is visible
            driver.execute_script("window.scrollTo({top: 0, behavior: 'instant'});")
            logger.info("✓ Scrolled to top")
            time.sleep(0.5)  # Brief wait for scroll to complete

            # Step 4: Verify header is visible
            try:
                header_wait = WebDriverWait(driver, 5)
                # Wait for header element to be visible in viewport
                header_element = header_wait.until(
                    EC.visibility_of_element_located((By.TAG_NAME, "header"))
                )
                logger.info("✓ Page header visible successfully")
            except TimeoutException:
                logger.warning("Header element not visible within 5s, but continuing...")
                # Take screenshot for debugging
                screenshot_manager = ScreenshotManager()
                screenshot_manager.capture_on_error(driver, "missing_header_after_search")
            except Exception as e:
                logger.warning(f"Error checking for header: {e}")

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


# ---------------------------------------------------------------------------
# Helpers for multi-process (no session management — pure driver functions)
# ---------------------------------------------------------------------------

def _multi_select_district(driver, district: str):
    """Select a district link on the current page."""
    wait = WebDriverWait(driver, 3)
    PopupBlocker.remove_blocking_overlays(driver)

    district_href_map = {
        "Central District": "CentralDistrict",
        "Eastern District": "EasternDistrict",
        "Northern District": "NorthernDistrict",
        "Southern District": "SouthernDistrict",
        "Western District": "WesternDistrict",
    }
    district_href = district_href_map.get(district, "")

    selectors = []
    if district_href:
        selectors += [
            (By.XPATH, f'//a[contains(@href, "{district_href}")]'),
            (By.CSS_SELECTOR, f'a[href*="{district_href}"]'),
        ]
    selectors += [
        (By.XPATH, f'//a[text()="{district}"]'),
        (By.XPATH, f'//a[contains(text(), "{district}")]'),
    ]

    element = None
    for by_type, sel in selectors:
        try:
            element = wait.until(EC.element_to_be_clickable((by_type, sel)))
            break
        except Exception:
            continue

    if not element:
        raise Exception(f"Cannot find district: {district}")

    driver.execute_script("arguments[0].scrollIntoView(true);", element)
    SmartWaits.wait_for_element_stable(driver, element, timeout=2)
    driver.execute_script("arguments[0].click();", element)
    SmartWaits.wait_for_page_ready(driver, timeout=2)
    logger.info(f"✓ Selected district: {district}")


def _multi_create_alert(driver):
    """Click the Create Alert menu then Create Docket Alert option."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    wait = WebDriverWait(driver, 2)
    SmartWaits.wait_for_page_ready(driver, timeout=2)

    # Remove blocking overlays using the shared utility (avoids querySelectorAll('*') crash)
    PopupBlocker.remove_blocking_overlays(driver)

    notification_icon = wait.until(
        EC.element_to_be_clickable((By.ID, "co_search_alertMenuLink"))
    )
    notification_icon.click()
    SmartWaits.wait_for_ajax_complete(driver, timeout=2)

    create_btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Create Docket Alert")]'))
    )
    create_btn.click()
    # Use longer timeout for new tabs — alert form takes longer to render
    SmartWaits.wait_for_page_ready(driver, timeout=5)
    SmartWaits.wait_for_ajax_complete(driver, timeout=3)
    logger.info("✓ Clicked Create Docket Alert")


def _multi_complete_alert_setup(driver, alert_name, alert_description, user_email, frequency, alert_times):
    """Fill and submit the complete alert setup form."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    import time

    # Use wider timeouts — new tabs need more render time than the main tab
    wait = WebDriverWait(driver, 8)
    SmartWaits.wait_for_page_ready(driver, timeout=5)

    # Alert name
    name_input = wait.until(EC.element_to_be_clickable((By.ID, "optionsAlertName")))
    name_input.click()
    time.sleep(0.05)
    name_input.clear()
    time.sleep(0.05)
    name_input.send_keys(alert_name)
    time.sleep(0.1)

    # Alert description (optional)
    if alert_description:
        desc_input = wait.until(EC.element_to_be_clickable((By.ID, "optionsAlertDescription")))
        desc_input.click()
        time.sleep(0.05)
        desc_input.clear()
        time.sleep(0.05)
        desc_input.send_keys(alert_description)
        time.sleep(0.1)

    # Continue (Basics)
    btn = wait.until(EC.element_to_be_clickable((By.ID, "co_button_continue_Basics")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", btn)
    SmartWaits.wait_for_ajax_complete(driver, timeout=2)

    # All Content tab
    all_content_tab = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//button[@role="tab"][@aria-controls="All_Content"]'))
    )
    all_content_tab.click()
    SmartWaits.wait_for_ajax_complete(driver, timeout=1)

    # Continue (Select Content)
    btn = wait.until(EC.element_to_be_clickable((By.ID, "co_button_continue_Content")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", btn)
    SmartWaits.wait_for_ajax_complete(driver, timeout=2)

    # Alert me to all new filings radio
    radio = wait.until(EC.element_to_be_clickable((By.ID, "co_search_alertMeToNewFilings")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", radio)
    time.sleep(0.3)
    try:
        radio.click()
    except Exception:
        driver.execute_script("arguments[0].click();", radio)
    time.sleep(0.15)

    # Continue (Enter Search Terms)
    btn = wait.until(EC.element_to_be_clickable((By.ID, "co_button_continue_Search")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", btn)
    SmartWaits.wait_for_ajax_complete(driver, timeout=2)

    # Email
    email_container = wait.until(
        EC.element_to_be_clickable((By.ID, "coid_contacts_addedContactsInput_co_collaboratorWidget"))
    )
    email_container.click()
    time.sleep(0.15)
    email_input = wait.until(EC.element_to_be_clickable((By.ID, "coid_contacts_autoSuggest_input")))
    email_input.clear()
    email_input.send_keys(user_email)
    time.sleep(0.15)
    email_input.send_keys(Keys.ENTER)
    SmartWaits.wait_for_ajax_complete(driver, timeout=2)

    # Continue (Customize delivery)
    btn = wait.until(EC.element_to_be_clickable((By.ID, "co_button_continue_Delivery")))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", btn)
    SmartWaits.wait_for_ajax_complete(driver, timeout=2)

    # Frequency
    freq_dropdown = wait.until(EC.presence_of_element_located((By.ID, "frequencySelect")))
    Select(freq_dropdown).select_by_value(frequency)
    time.sleep(0.15)

    # Alert times
    time_checkbox_ids = {
        "5am": "amExecutionTime5",
        "12pm": "pmExecutionTime12",
        "3pm": "pmExecutionTime3",
        "5pm": "pmExecutionTime5",
    }
    for label in alert_times:
        checkbox_id = time_checkbox_ids.get(label)
        if not checkbox_id:
            continue
        try:
            cb = wait.until(EC.presence_of_element_located((By.ID, checkbox_id)))
            if not cb.is_selected():
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
                time.sleep(0.2)
                try:
                    cb.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", cb)
            time.sleep(0.05)
        except Exception as e:
            logger.warning(f"Could not check {label} checkbox: {e}")

    # Save alert
    save_btn = wait.until(EC.element_to_be_clickable((By.ID, "co_button_saveAlert")))
    try:
        save_btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", save_btn)
    # Wait 10s for alert to actually save before tab gets closed
    time.sleep(10)
    logger.info("✓ Alert saved")


# ---------------------------------------------------------------------------
# Multi-docket endpoint
# ---------------------------------------------------------------------------

@app.post("/api/v1/docket/multi-process", response_model=MultiDocketResponse)
async def multi_process_dockets(request: MultiDocketRequest):
    """
    Process 1-20 dockets end-to-end (state → district → docket search → alert) using
    tab URL reuse: navigate to 'Select the state:' page once, then open new tabs
    with that URL for each additional docket instead of re-navigating from scratch.
    """
    if not (1 <= len(request.dockets) <= 20):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide 1 to 20 dockets"
        )

    if request.session_id not in browser_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    session_lock = session_locks.get(request.session_id)
    if not session_lock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session lock not found"
        )

    def _run_multi_process():
        with session_lock:
            session = browser_sessions[request.session_id]
            driver = session["driver"]
            main_handle = driver.current_window_handle

            docket_selector = DocketSelector()
            results = []

            # Step 1: Navigate to state selection page once and capture URL
            logger.info("Navigating to 'Select the state:' page...")
            state_page_url = docket_selector.navigate_to_state_page(driver)
            logger.info(f"State page URL: {state_page_url}")

            # Step 2: Process each docket sequentially
            for i, config in enumerate(request.dockets):
                logger.info(f"--- Processing docket {i+1}/{len(request.dockets)}: "
                             f"{config.docket_number} ({config.state}) ---")
                try:
                    if i > 0:
                        # Open new tab pre-loaded with the state selection page URL
                        logger.info(f"Opening new tab with state page URL for docket {i+1}...")
                        TabManager.open_tab_with_url(driver, state_page_url)
                        SmartWaits.wait_for_page_ready(driver, timeout=8)

                    # Select state
                    docket_selector.select_state_from_page(driver, config.state)

                    # Select district
                    _multi_select_district(driver, config.district)

                    # Search docket number (uses critical maxlength fix + char-by-char)
                    docket_selector.search_docket_number(driver, config.docket_number)

                    # Wait for search results page to fully render before creating alert.
                    # In single-docket flow this time comes from the HTTP round-trip +
                    # header visibility check (docket_routes.py:312-325). Without it
                    # Chrome's renderer crashes before it finishes painting.
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located((By.TAG_NAME, "header"))
                        )
                        logger.info("✓ Search results header visible")
                    except Exception:
                        logger.warning("Header not visible within 5s, continuing anyway")
                    time.sleep(1)  # Extra settle time for renderer

                    # Create alert
                    _multi_create_alert(driver)

                    # Give the alert form time to fully render before interacting
                    time.sleep(2)

                    # Complete alert setup form
                    _multi_complete_alert_setup(
                        driver,
                        config.alert_name,
                        config.alert_description or "",
                        config.user_email,
                        config.frequency,
                        config.alert_times,
                    )

                    results.append(MultiDocketResult(
                        docket_number=config.docket_number,
                        state=config.state,
                        status="success",
                        message="Alert created successfully",
                    ))
                    logger.info(f"✓ Docket {config.docket_number} completed")

                except Exception as e:
                    logger.error(f"✗ Docket {config.docket_number} failed: {e}")
                    screenshot_manager = ScreenshotManager()
                    screenshot_manager.capture_on_error(driver, f"multi_docket_error_{i}")
                    results.append(MultiDocketResult(
                        docket_number=config.docket_number,
                        state=config.state,
                        status="error",
                        message=str(e),
                    ))

                finally:
                    # Close current tab after each docket (success or fail) to prevent
                    # memory buildup — with 20 tabs Chrome crashes from memory pressure
                    if i > 0:
                        try:
                            driver.close()
                            driver.switch_to.window(main_handle)
                            logger.info(f"Closed tab for docket {i+1}, back to main")
                        except Exception:
                            pass
                    time.sleep(1)

            # Close extra tabs and return to main
            TabManager.close_extra_tabs(driver, main_handle)
            session["state"] = "multi_dockets_complete"

            all_ok = all(r.status == "success" for r in results)
            return results, "success" if all_ok else "partial"

    try:
        results, overall_status = await asyncio.to_thread(_run_multi_process)
        return MultiDocketResponse(status=overall_status, results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-process dockets failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multi-process dockets failed: {str(e)}"
        )
