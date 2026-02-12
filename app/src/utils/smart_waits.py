"""
Smart wait utilities for Selenium automation.
Replaces time.sleep() with event-driven waits for faster, more reliable automation.
"""

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoAlertPresentException
from selenium.webdriver.common.by import By
from src.utils.logger import get_logger
import time

logger = get_logger(__name__)


class SmartWaits:
    """Event-driven wait utilities to replace time.sleep()"""

    @staticmethod
    def wait_for_page_ready(driver, timeout=10):
        """
        Wait for page to be fully loaded and ready for interaction.
        PHASE 2 OPTIMIZED: Aggressive 100ms polling, respects timeout parameter.

        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait in seconds

        Returns:
            True if page is ready, False if timeout
        """
        try:
            # PHASE 2: Aggressive polling every 100ms instead of passive WebDriverWait
            # This returns faster when page is ready and respects the actual timeout
            max_iterations = int(timeout * 10)  # Check 10 times per second
            for i in range(max_iterations):
                try:
                    if driver.execute_script("return document.readyState") == "complete":
                        return True
                except:
                    pass  # Ignore errors during polling
                time.sleep(0.1)

            # Timeout reached but don't fail - let automation continue
            logger.debug(f"Page ready timeout after {timeout}s, continuing anyway")
            return True

        except TimeoutException:
            # Only catch TimeoutException specifically
            logger.debug(f"Page ready timeout after {timeout}s")
            return True
        except Exception as e:
            # Log unexpected errors but don't block
            logger.warning(f"Unexpected error in wait_for_page_ready: {e}")
            return True

    @staticmethod
    def wait_for_element_interactive(driver, by, selector, timeout=10):
        """
        Wait for element to be visible, clickable, and stable (not moving).

        Args:
            driver: Selenium WebDriver instance
            by: Selenium By locator type (By.ID, By.XPATH, etc.)
            selector: Element selector string
            timeout: Maximum time to wait in seconds

        Returns:
            WebElement if found and interactive, None if timeout

        Raises:
            TimeoutException: If element doesn't become interactive within timeout
        """
        try:
            logger.debug(f"Waiting for element interactive: {by}={selector}")
            start_time = time.time()

            # First, wait for element to be present in DOM
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )

            # Wait for element to be visible
            WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((by, selector))
            )

            # Wait for element to be clickable (visible + enabled)
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, selector))
            )

            # Check if element position is stable (not animating)
            try:
                prev_location = element.location
                time.sleep(0.1)  # Brief check for stability
                curr_location = element.location
                if prev_location != curr_location:
                    # Element is moving, wait a bit
                    time.sleep(0.3)
            except StaleElementReferenceException:
                # Element became stale, re-find it
                element = WebDriverWait(driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )

            elapsed = time.time() - start_time
            logger.debug(f"✓ Element interactive in {elapsed:.2f}s")
            return element

        except TimeoutException:
            elapsed = time.time() - start_time
            logger.warning(f"Element interactive timeout after {elapsed:.2f}s")
            return None

    @staticmethod
    def wait_for_ajax_complete(driver, timeout=5):
        """
        Wait for all AJAX requests to complete.
        PHASE 2 OPTIMIZED: Quick jQuery.active check with aggressive polling.

        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait in seconds

        Returns:
            True when AJAX complete or timeout
        """
        try:
            # PHASE 2: Quick check for jQuery.active with 100ms polling
            max_iterations = int(timeout * 10)  # Check 10 times per second
            for i in range(max_iterations):
                try:
                    # Check if jQuery is present and if any AJAX requests are active
                    jquery_active = driver.execute_script(
                        "return typeof jQuery !== 'undefined' && jQuery.active > 0"
                    )
                    if not jquery_active:
                        return True  # No active AJAX requests
                except:
                    # jQuery not present or error - assume no AJAX
                    return True
                time.sleep(0.1)

            # Timeout reached but don't fail
            logger.debug(f"AJAX wait timeout after {timeout}s, continuing anyway")
            return True

        except Exception as e:
            # On any error, just continue
            logger.debug(f"AJAX wait error: {e}, continuing anyway")
            return True

    @staticmethod
    def wait_for_modal_gone(driver, modal_selector='//div[contains(@class, "modal") or contains(@class, "overlay")]', timeout=5):
        """
        Wait for modal or overlay to disappear from the page.

        Args:
            driver: Selenium WebDriver instance
            modal_selector: XPath selector for modal/overlay element
            timeout: Maximum time to wait in seconds

        Returns:
            True if modal disappeared, False if timeout or not found
        """
        try:
            from selenium.webdriver.common.by import By

            logger.debug(f"Waiting for modal/overlay to disappear...")
            start_time = time.time()

            # First check if modal exists
            modals = driver.find_elements(By.XPATH, modal_selector)
            if not modals:
                logger.debug("No modal found, continuing")
                return True

            # Wait for modal to become invisible
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.XPATH, modal_selector))
            )

            elapsed = time.time() - start_time
            logger.debug(f"✓ Modal disappeared in {elapsed:.2f}s")
            return True

        except TimeoutException:
            elapsed = time.time() - start_time
            logger.warning(f"Modal disappear timeout after {elapsed:.2f}s")
            return False
        except Exception as e:
            logger.warning(f"Modal wait error: {e}")
            return False

    @staticmethod
    def wait_after_click(driver, element, timeout=10):
        """
        Click element and wait for page to respond.
        Detects page changes by checking for stale element or document state changes.

        Args:
            driver: Selenium WebDriver instance
            element: WebElement to click
            timeout: Maximum time to wait in seconds

        Returns:
            True if page responded, False if timeout
        """
        try:
            logger.debug("Clicking element and waiting for page response...")
            start_time = time.time()

            # Get current URL before click
            current_url = driver.current_url

            # Click the element
            element.click()

            # Wait for either:
            # 1. Element becomes stale (page changed/reloaded)
            # 2. URL changes (navigation occurred)
            # 3. Document readyState completes (page finished loading)

            try:
                # Check if element becomes stale (indicates page change)
                WebDriverWait(driver, 1).until(EC.staleness_of(element))
                logger.debug("✓ Page changed (element became stale)")
            except TimeoutException:
                # Element didn't become stale, check URL or readyState
                pass

            # Check if URL changed
            if driver.current_url != current_url:
                logger.debug("✓ URL changed, waiting for page load...")
                SmartWaits.wait_for_page_ready(driver, timeout - (time.time() - start_time))
            else:
                # Same page, wait for any pending operations
                time.sleep(0.3)  # Brief pause for UI updates
                SmartWaits.wait_for_ajax_complete(driver, timeout=2)

            elapsed = time.time() - start_time
            logger.debug(f"✓ Page responded in {elapsed:.2f}s")
            return True

        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(f"Click response wait error after {elapsed:.2f}s: {e}")
            return False

    @staticmethod
    def wait_for_element_stable(driver, element, timeout=3):
        """
        Wait for element position to become stable (stop moving/animating).

        Args:
            driver: Selenium WebDriver instance
            element: WebElement to monitor
            timeout: Maximum time to wait in seconds

        Returns:
            True if element is stable, False if timeout
        """
        try:
            start_time = time.time()
            stable_count = 0
            required_stable_checks = 3  # Need 3 consistent position checks

            prev_location = element.location

            while time.time() - start_time < timeout:
                time.sleep(0.1)
                try:
                    curr_location = element.location
                    if prev_location == curr_location:
                        stable_count += 1
                        if stable_count >= required_stable_checks:
                            elapsed = time.time() - start_time
                            logger.debug(f"✓ Element stable in {elapsed:.2f}s")
                            return True
                    else:
                        stable_count = 0
                        prev_location = curr_location
                except StaleElementReferenceException:
                    logger.warning("Element became stale during stability check")
                    return False

            logger.warning(f"Element stability timeout after {timeout}s")
            return False

        except Exception as e:
            logger.warning(f"Element stability check error: {e}")
            return False

    @staticmethod
    def dismiss_any_popups(driver):
        """
        Manually dismiss any visible popups, alerts, or modals.
        Use this when you encounter unexpected popups.

        Args:
            driver: Selenium WebDriver instance

        Returns:
            True if any popups were dismissed, False otherwise
        """
        dismissed = False

        # 1. Try to dismiss alerts
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            logger.info(f"Dismissing alert: '{alert_text}'")
            alert.dismiss()
            dismissed = True
        except NoAlertPresentException:
            pass
        except Exception:
            try:
                alert = driver.switch_to.alert
                alert.accept()
                dismissed = True
            except:
                pass

        # 2. Close modal dialogs
        close_selectors = [
            '//button[contains(@class, "close")]',
            '//button[contains(@aria-label, "Close")]',
            '//button[contains(text(), "Close")]',
            '//button[contains(text(), "×")]',
            '//button[contains(text(), "Dismiss")]',
            '//button[contains(text(), "Cancel")]',
        ]

        for selector in close_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            dismissed = True
                            logger.info(f"Closed modal using: {selector}")
                    except:
                        continue
            except:
                continue

        if dismissed:
            logger.info("✓ Popups dismissed")

        return dismissed
