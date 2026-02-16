"""
Alert creation and configuration endpoints.
"""

import sys
import asyncio
from pathlib import Path

from fastapi import HTTPException, status

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import get_logger
from src.utils.smart_waits import SmartWaits
from src.utils.popup_blocker import PopupBlocker
from api.app import app, browser_sessions, session_locks
from models.schemas import (
    CreateAlertRequest,
    CreateAlertResponse,
    CompleteAlertSetupRequest,
    CompleteAlertSetupResponse,
)

logger = get_logger(__name__)


@app.post("/api/v1/alert/create", response_model=CreateAlertResponse)
async def create_alert(request: CreateAlertRequest):
    """
    Create a docket alert by clicking the notification icon and selecting 'Create Docket Alert'.
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

    def _create_alert_with_lock():
        with session_lock:
            session = browser_sessions[request.session_id]
            driver = session["driver"]

            logger.info(f"Creating alert for session {request.session_id}")

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            import time

            # OPTIMIZED: Reduced timeout from 3s to 2s
            wait = WebDriverWait(driver, 2)
            # OPTIMIZED: Use smart wait instead of fixed sleep (reduced from 3s to 2s)
            SmartWaits.wait_for_page_ready(driver, timeout=2)

            # Enhanced overlay removal
            logger.info("Removing blocking overlays and dropdowns...")
            try:
                # Remove high z-index overlays
                removed_overlays = driver.execute_script("""
                    var removed = 0;

                    // Remove high z-index overlays (including modals, dropdowns)
                    document.querySelectorAll('*').forEach(function(el) {
                        try {
                            var style = window.getComputedStyle(el);
                            var zIndex = parseInt(style.zIndex);

                            // Lower threshold to 500 (instead of 1000)
                            if (zIndex > 500 &&
                                (style.position === 'fixed' || style.position === 'absolute') &&
                                style.display !== 'none') {

                                // Don't remove main navigation
                                if (!el.closest('header') && !el.closest('nav')) {
                                    console.log('Removing overlay with z-index: ' + zIndex);
                                    el.remove();
                                    removed++;
                                }
                            }
                        } catch(e) {}
                    });

                    // Remove specific dropdown classes that block clicks
                    document.querySelectorAll('.co_formTextSelect, .dropdown-menu, .autocomplete').forEach(function(el) {
                        if (window.getComputedStyle(el).display !== 'none') {
                            console.log('Removing blocking dropdown:', el.className);
                            el.remove();
                            removed++;
                        }
                    });

                    return removed;
                """)

                if removed_overlays > 0:
                    logger.info(f"✓ Removed {removed_overlays} blocking element(s)")
                    time.sleep(0.2)  # Brief wait after removal
            except Exception as e:
                logger.warning(f"Overlay removal failed: {e}")

            # Find and click "Create Alert menu" button
            notification_selectors = [
                (By.ID, 'co_search_alertMenuLink'),
                (By.XPATH, '//button[@id="co_search_alertMenuLink"]'),
            ]

            notification_icon = None
            for by, selector in notification_selectors:
                try:
                    notification_icon = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    break
                except:
                    continue

            if not notification_icon:
                raise Exception("Cannot find 'Create Alert menu' button")

            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            notification_icon.click()
            # OPTIMIZED: Wait for menu to appear instead of fixed sleep
            SmartWaits.wait_for_ajax_complete(driver, timeout=2)

            # Find and click "Create Docket Alert" option
            create_alert_selectors = [
                (By.XPATH, '//a[contains(text(), "Create Docket Alert")]'),
                (By.XPATH, '//button[contains(text(), "Create Docket Alert")]'),
            ]

            create_alert_button = None
            for by, selector in create_alert_selectors:
                try:
                    create_alert_button = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    break
                except:
                    continue

            if not create_alert_button:
                raise Exception("Cannot find 'Create Docket Alert' option")

            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            create_alert_button.click()
            # OPTIMIZED: Wait for alert form to load (reduced from 3s to 2s)
            SmartWaits.wait_for_page_ready(driver, timeout=2)

            session["state"] = "alert_created"
            return True

    try:
        await asyncio.to_thread(_create_alert_with_lock)

        return CreateAlertResponse(
            status="success",
            message="Successfully clicked 'Create Docket Alert'"
        )

    except Exception as e:
        logger.error(f"Create alert failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Create alert failed: {str(e)}"
        )


@app.post("/api/v1/alert/complete-setup", response_model=CompleteAlertSetupResponse)
async def complete_alert_setup(request: CompleteAlertSetupRequest):
    """
    Complete the alert setup by filling all form fields and saving.
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

    def _complete_setup_with_lock():
        with session_lock:
            session = browser_sessions[request.session_id]
            driver = session["driver"]

            logger.info(f"Completing alert setup for session {request.session_id}")

            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.support.ui import WebDriverWait, Select
            from selenium.webdriver.support import expected_conditions as EC
            import time

            # OPTIMIZED: Reduced timeout from 3s to 2s
            wait = WebDriverWait(driver, 2)
            # OPTIMIZED: Wait for page to be ready (reduced from 3s to 2s)
            SmartWaits.wait_for_page_ready(driver, timeout=2)

            # Enhanced overlay removal
            logger.info("Removing blocking overlays and dropdowns...")
            try:
                # Remove high z-index overlays
                removed_overlays = driver.execute_script("""
                    var removed = 0;

                    // Remove high z-index overlays (including modals, dropdowns)
                    document.querySelectorAll('*').forEach(function(el) {
                        try {
                            var style = window.getComputedStyle(el);
                            var zIndex = parseInt(style.zIndex);

                            // Lower threshold to 500 (instead of 1000)
                            if (zIndex > 500 &&
                                (style.position === 'fixed' || style.position === 'absolute') &&
                                style.display !== 'none') {

                                // Don't remove main navigation
                                if (!el.closest('header') && !el.closest('nav')) {
                                    console.log('Removing overlay with z-index: ' + zIndex);
                                    el.remove();
                                    removed++;
                                }
                            }
                        } catch(e) {}
                    });

                    // Remove specific dropdown classes that block clicks
                    document.querySelectorAll('.co_formTextSelect, .dropdown-menu, .autocomplete').forEach(function(el) {
                        if (window.getComputedStyle(el).display !== 'none') {
                            console.log('Removing blocking dropdown:', el.className);
                            el.remove();
                            removed++;
                        }
                    });

                    return removed;
                """)

                if removed_overlays > 0:
                    logger.info(f"✓ Removed {removed_overlays} blocking element(s)")
                    time.sleep(0.2)  # Brief wait after removal
            except Exception as e:
                logger.warning(f"Overlay removal failed: {e}")

            # Fill alert name
            logger.info("Filling alert name...")
            name_input = wait.until(
                EC.element_to_be_clickable((By.ID, "optionsAlertName"))
            )
            # Click to focus the field first
            name_input.click()
            time.sleep(0.05)
            # Clear any existing content
            name_input.clear()
            time.sleep(0.05)
            # Enter the alert name
            name_input.send_keys(request.alert_name)
            logger.info(f"Alert name entered: {request.alert_name}")
            # OPTIMIZED: Brief wait for field to register input
            time.sleep(0.1)

            # Fill description if provided
            if request.alert_description:
                logger.info("Filling alert description...")
                description_input = wait.until(
                    EC.element_to_be_clickable((By.ID, "optionsAlertDescription"))
                )
                # Click to focus the field first
                description_input.click()
                time.sleep(0.05)
                # Clear any existing content
                description_input.clear()
                time.sleep(0.05)
                # Enter the description
                description_input.send_keys(request.alert_description)
                logger.info("Description entered")
                # OPTIMIZED: Brief wait for field to register input
                time.sleep(0.1)

            # Click Continue (Basics)
            logger.info("Clicking Continue (Basics) button...")
            continue_button = wait.until(
                EC.element_to_be_clickable((By.ID, "co_button_continue_Basics"))
            )
            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            continue_button.click()
            logger.info("✓ Clicked Continue (Basics)")
            # OPTIMIZED: Removed redundant SmartWaits - next element wait is sufficient

            # Click "All Content" tab
            all_content_tab = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//button[@role="tab"][@aria-controls="All_Content"]'))
            )
            all_content_tab.click()
            # OPTIMIZED: Wait for tab content to load
            SmartWaits.wait_for_ajax_complete(driver, timeout=1)

            # Click Continue (Select Content)
            continue_content_button = wait.until(
                EC.element_to_be_clickable((By.ID, "co_button_continue_Content"))
            )
            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            continue_content_button.click()
            # OPTIMIZED: Removed redundant SmartWaits - next element wait is sufficient

            # Click "Alert me to all new filings" radio
            new_filings_radio = wait.until(
                EC.element_to_be_clickable((By.ID, "co_search_alertMeToNewFilings"))
            )
            logger.info("✓ Found 'Alert me to all new filings' radio button")

            # Scroll into view first
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", new_filings_radio)
            time.sleep(0.3)

            try:
                new_filings_radio.click()
                logger.info("✓ Clicked radio button using regular click")
            except Exception as e:
                logger.warning(f"Regular click failed: {e}. Trying JavaScript click...")
                driver.execute_script("arguments[0].click();", new_filings_radio)
                logger.info("✓ Clicked radio button using JavaScript click")

            time.sleep(0.15)

            # Click Continue (Enter Search Terms)
            continue_search_button = wait.until(
                EC.element_to_be_clickable((By.ID, "co_button_continue_Search"))
            )
            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            continue_search_button.click()
            # OPTIMIZED: Removed redundant SmartWaits - next element wait is sufficient

            # Fill email
            email_container = wait.until(
                EC.element_to_be_clickable((By.ID, "coid_contacts_addedContactsInput_co_collaboratorWidget"))
            )
            email_container.click()
            # OPTIMIZED: Reduced from 0.3s to 0.15s
            time.sleep(0.15)

            email_input = wait.until(
                EC.element_to_be_clickable((By.ID, "coid_contacts_autoSuggest_input"))
            )
            email_input.clear()
            email_input.send_keys(request.user_email)
            # OPTIMIZED: Reduced from 0.3s to 0.15s
            time.sleep(0.15)
            email_input.send_keys(Keys.ENTER)
            # OPTIMIZED: Wait for email to be added
            SmartWaits.wait_for_ajax_complete(driver, timeout=2)

            # Click Continue (Customize delivery)
            continue_delivery_button = wait.until(
                EC.element_to_be_clickable((By.ID, "co_button_continue_Delivery"))
            )
            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            continue_delivery_button.click()
            # OPTIMIZED: Removed redundant SmartWaits - next element wait is sufficient

            # Select frequency
            frequency_dropdown = wait.until(
                EC.presence_of_element_located((By.ID, "frequencySelect"))
            )
            select = Select(frequency_dropdown)
            select.select_by_value(request.frequency)
            # OPTIMIZED: Reduced from 0.3s to 0.15s
            time.sleep(0.15)

            # Check alert times
            time_checkbox_ids = {
                '5am': 'amExecutionTime5',
                '12pm': 'pmExecutionTime12',
                '3pm': 'pmExecutionTime3',
                '5pm': 'pmExecutionTime5'
            }

            for time_label in request.alert_times:
                if time_label in time_checkbox_ids:
                    checkbox_id = time_checkbox_ids[time_label]
                    try:
                        checkbox = wait.until(
                            EC.presence_of_element_located((By.ID, checkbox_id))
                        )
                        if not checkbox.is_selected():
                            # Scroll into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                            time.sleep(0.2)

                            try:
                                checkbox.click()
                                logger.info(f"✓ Checked {time_label} checkbox using regular click")
                            except:
                                driver.execute_script("arguments[0].click();", checkbox)
                                logger.info(f"✓ Checked {time_label} checkbox using JavaScript click")

                        time.sleep(0.05)
                    except Exception as e:
                        logger.warning(f"Could not check {time_label} checkbox: {e}")

            # Click "Save alert" button
            save_alert_button = wait.until(
                EC.element_to_be_clickable((By.ID, "co_button_saveAlert"))
            )
            # PHASE 1 OPTIMIZATION: Overlays already removed at start
            save_alert_button.click()
            # OPTIMIZED: Wait for save confirmation (reduced from 3s to 2s)
            SmartWaits.wait_for_page_ready(driver, timeout=2)

            session["state"] = "alert_setup_complete"
            return True

    try:
        await asyncio.to_thread(_complete_setup_with_lock)

        return CompleteAlertSetupResponse(
            status="success",
            message="Alert setup completed successfully"
        )

    except Exception as e:
        logger.error(f"Complete alert setup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Complete alert setup failed: {str(e)}"
        )
